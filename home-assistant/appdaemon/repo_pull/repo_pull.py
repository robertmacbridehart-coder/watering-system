"""repo_pull.py -- AppDaemon app: guarded, event-triggered public-repo pull.

WHY THIS EXISTS
---------------
The 2025-10-05 incident (docs/repo_pull_incident_report.md) closed against the
HAOS `shell_command` integration: it executed fine from Developer Tools but
never ran reliably from a script/automation context, and returned cached output
that lied about execution. The accepted workaround was a manual SSH pull.

Since then AppDaemon has been deployed on the HA Green and is proven, in this
same project, to (a) listen for HA bus events and (b) write into /homeassistant/
reliably -- see home-assistant/appdaemon/watering_db/db_export.py. That clears
every failure mode in the incident report, because this app runs the pull as a
real OS subprocess from AppDaemon's own Python, NOT through `shell_command`.

WHAT IT DOES (guarded pipeline)
-------------------------------
Triggered by the HA bus event `watering_repo_pull` (fired by the input_button
automation in home-assistant/packages/repo_pull.yaml):

  1. PREFLIGHT INTERLOCK (fail-closed) -- abort the whole pull if watering is
     active: any watering relay ON (hardware ground truth) or the state machine
     in an active (actuating) state. The parked control states (manual_override,
     winterized) do NOT block -- relays are de-energized there and the park
     survives the auto-restart. Never swap config files or restart HA while a
     pump or valve is energized.
  2. BACKUP -- create a partial (HA-config-only) backup and wait for it before
     touching any file. If the backup cannot be confirmed, abort.
  3. PULL -- run home-assistant/scripts/pull_public_repo.sh as a subprocess
     (single source of truth for the file map: config, packages, scripts,
     esphome, appdaemon apps, version files). Runs in a worker thread so the
     ~40 s of blocking I/O cannot stall AppDaemon's scheduler.
  4. VALIDATE -- ask Supervisor to check the config (POST /core/check). The
     restart is gated on a POSITIVE "valid" result. If validity cannot be
     confirmed (endpoint unavailable / insufficient add-on role), the pull is
     kept but the restart is SKIPPED and the user is told to restart manually --
     restarting into an unverified config is the one thing that can break boot.
  5. APPLY -- full HA restart, only when validation returned valid and
     `auto_restart` is enabled.

Every stage writes a persistent notification and a `system_events` audit row
(the durable record; verify by side-effect, per programming-notes.md).

apps.yaml configuration (see the sibling apps.yaml for the deployed values):
  trigger_event        -- HA event this app listens for
  pull_script          -- absolute path to pull_public_repo.sh on the Green
  version_json         -- version.json written by the pull (used to prove the
                          pull actually changed files, not just returned 0)
  db_path              -- watering_ops.db, for audit rows (optional; skipped if
                          the file is absent)
  relay_entities       -- switch entity_ids whose ON state blocks a pull
  state_entity         -- input_select the state machine drives
  active_states        -- states of state_entity that block a pull (parked
                          control states manual_override/winterized excluded)
  backup_name_prefix   -- name prefix for the pre-pull partial backup
  backup_state_entity  -- sensor that reports backup-manager activity (optional)
  auto_restart         -- restart HA after a validated pull (default true)
  subprocess_timeout   -- hard cap (seconds) on the pull subprocess
"""

import json
import os
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import appdaemon.plugins.hass.hassapi as hass


class RepoPull(hass.Hass):
    """Guarded, event-triggered pull of the public repo into HA config."""

    # ---- lifecycle -------------------------------------------------------

    def initialize(self):
        self.trigger_event = self.args.get("trigger_event", "watering_repo_pull")
        self.pull_script = self.args.get(
            "pull_script", "/homeassistant/scripts/pull_public_repo.sh"
        )
        self.version_json = self.args.get(
            "version_json", "/homeassistant/version.json"
        )
        self.db_path = self.args.get("db_path", "/homeassistant/watering_ops.db")

        self.relay_entities = self.args.get("relay_entities", [])
        self.state_entity = self.args.get(
            "state_entity", "input_select.watering_system_state"
        )
        self.active_states = set(self.args.get("active_states", []))

        self.backup_name_prefix = self.args.get(
            "backup_name_prefix", "pre_repo_pull"
        )
        # How long to wait for the (awaited) partial backup to finish. Must be
        # generous: the default AppDaemon hass_timeout (~10 s) gives up mid-job.
        self.backup_timeout = int(self.args.get("backup_timeout", 300))
        self.auto_restart = bool(self.args.get("auto_restart", True))
        self.subprocess_timeout = int(self.args.get("subprocess_timeout", 300))

        # One pull at a time. The event can be fired repeatedly (button mashing);
        # a second pull while one is running would race on the same files.
        self._lock = threading.Lock()

        self.listen_event(self.on_trigger, self.trigger_event)
        self.log(
            f"RepoPull ready; listening for '{self.trigger_event}'", level="INFO"
        )

    # ---- entry point -----------------------------------------------------

    def on_trigger(self, event_name, data, kwargs):
        """Handle the trigger event; run the pipeline in a worker thread.

        The callback returns immediately so AppDaemon's scheduler is never
        blocked by the ~40 s pull (the user's chosen execution model).
        """
        if not self._lock.acquire(blocking=False):
            self.log("Repo pull already in progress; ignoring trigger.", level="WARNING")
            self._notify("Repo Pull Skipped", "A pull is already running.")
            return
        try:
            threading.Thread(
                target=self._run_pipeline, name="repo_pull", daemon=True
            ).start()
        except Exception as exc:  # noqa: BLE001 - never leak the lock on spawn failure
            self._lock.release()
            self.error(f"Could not start repo pull worker thread: {exc}")
            self._notify("Repo Pull Failed", f"Could not start pull worker: {exc}")

    def _run_pipeline(self):
        """The guarded pipeline. Runs in a worker thread; releases the lock."""
        try:
            # 1. PREFLIGHT INTERLOCK -----------------------------------------
            blocked_reason = self._preflight_block_reason()
            if blocked_reason is not None:
                msg = f"Aborted: {blocked_reason}. No backup, no pull, no restart."
                self.log(f"Repo pull {msg}", level="WARNING")
                self._audit("repo_pull", "warning", msg)
                self._notify("Repo Pull Aborted", msg)
                return

            # 2. BACKUP ------------------------------------------------------
            if not self._create_backup():
                msg = "Aborted: pre-pull backup could not be confirmed."
                self.log(f"Repo pull {msg}", level="ERROR")
                self._audit("repo_pull", "critical", msg)
                self._notify("Repo Pull Aborted", msg)
                return

            # 3. PULL --------------------------------------------------------
            ok, detail = self._run_pull_script()
            if not ok:
                msg = f"Pull FAILED: {detail}. Backup retained; no restart."
                self.log(f"Repo pull {msg}", level="ERROR")
                self._audit("repo_pull", "critical", msg)
                self._notify("Repo Pull Failed", msg)
                return

            # 4. VALIDATE ----------------------------------------------------
            valid, vdetail = self._check_config()

            # 5. APPLY -------------------------------------------------------
            if valid and self.auto_restart:
                msg = f"Pull OK ({detail}); config valid. Restarting Home Assistant."
                self.log(f"Repo pull {msg}", level="INFO")
                self._audit("repo_pull", "info", msg)
                self._notify("Repo Pull Succeeded", msg)
                # Give the notification/audit write a moment to land, then restart.
                time.sleep(2)
                self.call_service("homeassistant/restart")
                return

            if valid and not self.auto_restart:
                msg = f"Pull OK ({detail}); config valid. Auto-restart disabled -- restart HA to apply."
            else:
                # Not positively valid -> fail safe, never auto-restart.
                msg = (
                    f"Pull OK ({detail}) but config validation was {vdetail}. "
                    "Restart SKIPPED -- review config, then restart Home Assistant "
                    "manually. The pre-pull backup can restore the previous state."
                )
            self.log(f"Repo pull {msg}", level="WARNING")
            self._audit("repo_pull", "warning", msg)
            self._notify("Repo Pull -- Manual Restart Needed", msg)
        except Exception as exc:  # noqa: BLE001 - last-resort guard for a worker thread
            msg = f"Unexpected error in repo pull pipeline: {exc}"
            self.error(msg)
            self._audit("repo_pull", "critical", msg)
            self._notify("Repo Pull Failed", msg)
        finally:
            self._lock.release()

    # ---- stage 1: interlock ---------------------------------------------

    def _preflight_block_reason(self):
        """Return a human string if a pull must be blocked, else None.

        Fail-closed on actuation. Two independent signals:
          * any watering relay reporting 'on' (hardware ground truth -- the
            load-bearing check);
          * the state machine in an active (actuating / mid-cycle) state.
        The PARKED control states (manual_override, winterized) and error-idle
        states are deliberately NOT blockers: relays are de-energized in all of
        them, and deploying a fix while parked or in an error state must remain
        possible. manual_override is the end-of-testing park SOP, so requiring an
        un-park before every pull was pure friction; the relay-ON check still
        blocks if manual toggling has actually energized a relay. (The former
        manual_override boolean interlock was removed 2026-08-18 for this reason.)
        An 'unavailable'/'unknown' relay is treated as NOT blocking: a pull +
        restart issues no relay commands, and an offline ESP32 leaves relays
        physically de-energized (ALWAYS_OFF). Deploying a fix while the ESP is
        offline must remain possible.
        """
        for entity in self.relay_entities:
            state = self.get_state(entity)
            if state == "on":
                return f"relay {entity} is ON"

        if self.active_states:
            current = self.get_state(self.state_entity)
            if current in self.active_states:
                return f"system state is '{current}'"

        return None

    # ---- stage 2: backup -------------------------------------------------

    def _create_backup(self):
        """Create a partial (HA-config-only) backup and wait for it to finish.

        Uses the Supervisor `hassio.backup_partial` action (config-only is not
        available via the newer `backup.create`, which is full-instance).
        homeassistant=True backs up just the HA Core config folder -- fast, and
        exactly what the pull can damage.

        The call is routed through HA Core, which awaits the Supervisor backup
        job, so a generous `hass_timeout` makes AppDaemon block until the backup
        is actually written. Verified on the Green 2026-07-01: the backup lands
        in seconds; the earlier failure was purely AppDaemon's ~10 s default
        hass_timeout giving up mid-job and logging a misleading "complete". If
        the call raises, the backup is treated as failed and the pull aborts.
        """
        name = f"{self.backup_name_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log(
            f"Creating pre-pull partial backup '{name}' "
            f"(waiting up to {self.backup_timeout}s)...",
            level="INFO",
        )
        try:
            self.call_service(
                "hassio/backup_partial",
                name=name,
                homeassistant=True,
                addons=[],
                folders=[],
                hass_timeout=self.backup_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            self.error(f"backup_partial call failed: {exc}")
            return False

        self.log(f"Pre-pull backup '{name}' complete.", level="INFO")
        return True

    # ---- stage 3: pull ---------------------------------------------------

    def _run_pull_script(self):
        """Run pull_public_repo.sh as a subprocess. Verify by side-effect.

        Returns (ok, detail). Success requires BOTH a zero exit code AND a fresh
        version.json (mtime advanced) -- the incident report's core lesson was
        that exit status alone lied about execution.
        """
        if not os.path.exists(self.pull_script):
            return False, f"pull script not found at {self.pull_script}"

        before_mtime = self._version_mtime()

        env = dict(os.environ)
        # AppDaemon owns validation + restart, so tell the script to skip its own
        # (its `ha core check` branch is unavailable in this container anyway).
        env["PULL_SKIP_VALIDATE"] = "1"

        self.log(f"Running pull script: {self.pull_script}", level="INFO")
        try:
            result = subprocess.run(
                ["/bin/sh", self.pull_script],
                env=env,
                capture_output=True,
                text=True,
                timeout=self.subprocess_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, f"pull script exceeded {self.subprocess_timeout}s timeout"
        except OSError as exc:
            return False, f"could not execute pull script: {exc}"

        tail = (result.stdout or "").strip().splitlines()[-5:]
        self.log("pull script output (tail): " + " | ".join(tail), level="INFO")
        if result.returncode != 0:
            err = (result.stderr or "").strip()[-300:]
            return False, f"exit {result.returncode}: {err or 'see AppDaemon log'}"

        after_mtime = self._version_mtime()
        if after_mtime is None:
            return False, "version.json missing after pull (files may not have written)"
        if before_mtime is not None and after_mtime <= before_mtime:
            return False, "version.json not updated (pull did not write files)"

        return True, self._version_summary()

    def _version_mtime(self):
        try:
            return os.path.getmtime(self.version_json)
        except OSError:
            return None

    def _version_summary(self):
        """Short 'tag@sha' string from version.json, for notifications."""
        try:
            with open(self.version_json, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            sha = (data.get("sha") or "unknown")[:7]
            return f"{data.get('tag', 'unknown')}@{sha}"
        except (OSError, ValueError):
            return "version unknown"

    # ---- stage 4: validation --------------------------------------------

    def _check_config(self):
        """Validate the config via the HA Core API. Returns (valid, detail).

        Uses the Home Assistant Core endpoint POST /api/config/core/check_config
        through the Supervisor's `homeassistant_api` proxy
        (http://supervisor/core/api/...) with SUPERVISOR_TOKEN -- the same proxy
        path pull_public_repo.sh already uses. This is deliberately NOT the
        Supervisor-native /core/check endpoint, which needs an elevated
        hassio_role the add-on does not have (it returned 403). The Core endpoint
        only needs homeassistant_api access, which the add-on has.

        Only an explicit {"result": "valid"} counts as valid; anything else
        (invalid config, no token, HTTP failure) returns valid=False so the
        caller fails safe and does not auto-restart.
        """
        token = os.environ.get("SUPERVISOR_TOKEN")
        if not token:
            return False, "unverified (no SUPERVISOR_TOKEN in AppDaemon container)"

        request = urllib.request.Request(
            "http://supervisor/core/api/config/core/check_config",
            data=b"",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return False, f"unverified (HTTP {exc.code} from check_config)"
        except (urllib.error.URLError, ValueError, OSError) as exc:
            return False, f"unverified (check_config error: {exc})"

        if payload.get("result") == "valid":
            return True, "valid"
        errors = payload.get("errors") or json.dumps(payload)[:300]
        return False, f"INVALID: {errors}"

    # ---- helpers ---------------------------------------------------------

    def _notify(self, title, message):
        """Create a persistent notification (stable id so it self-replaces)."""
        try:
            self.call_service(
                "persistent_notification/create",
                title=title,
                message=message,
                notification_id="repo_pull_status",
            )
        except Exception as exc:  # noqa: BLE001
            self.error(f"Could not create persistent notification: {exc}")

    def _audit(self, event_type, severity, notes):
        """Best-effort audit row in watering_ops.system_events.

        Mirrors db_export.py's pattern. Silently skipped if the DB is absent so a
        pull is never blocked by DB state.
        """
        if not os.path.exists(self.db_path):
            return
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute(
                "INSERT INTO system_events "
                "(timestamp, event_type, severity, notes) VALUES (?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    event_type,
                    severity,
                    notes,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            self.error(f"Could not write repo_pull audit row: {exc}")
        finally:
            if conn is not None:
                conn.close()
