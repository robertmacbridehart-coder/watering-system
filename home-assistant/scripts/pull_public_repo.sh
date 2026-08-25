#!/bin/sh
set -eu

# --- REPO SETTINGS ---
OWNER="robertmacbridehart-coder"
REPO="watering-system"
BRANCH="main"

# Repo layout (public repo)
REPO_HA_ROOT="home-assistant"
REPO_ESP_ROOT="esphome"

# HA layout (your system root)
HA_ROOT="/homeassistant"
HA_CFG="$HA_ROOT/configuration.yaml"
HA_PKG="$HA_ROOT/packages"
HA_ESP="$HA_ROOT/esphome"
HA_SCRIPTS="$HA_ROOT/scripts"
# AppDaemon deploy target: app_dir is /homeassistant/appdaemon/apps (see
# docs/db_setup_guide.md). Every home-assistant/appdaemon/<app>/ folder in the
# repo is deployed under HA_AD_ROOT/<app>/ (see the deploy loop below). The
# watering_db app additionally gets a runtime copy of the canonical
# docs/db_schema.sql.
HA_AD_ROOT="$HA_ROOT/appdaemon/apps"
HA_AD_DB="$HA_AD_ROOT/watering_db"
HA_BACKUP_DIR="$HA_ROOT/.backups"
# Version files for the About dashboard
VER_TXT="$HA_ROOT/version.txt"
VER_JSON="$HA_ROOT/version.json"

# Dry-run: with PULL_DRY_RUN=1 the script previews what a real pull would delete
# or change and writes NOTHING. Previewing deletions is only meaningful when rsync
# is installed -- only rsync --delete removes files; the cp fallback never deletes.
DRY_RUN="${PULL_DRY_RUN:-0}"

# ---- helpers ----
have() { command -v "$1" >/dev/null 2>&1; }

notify() {
  title="$1"; msg="$2"; nid="repo_pull_status"
  if [ -n "${SUPERVISOR_TOKEN-}" ] && have curl; then
    { set +x; } 2>/dev/null
    curl -fsSL -X POST \
      -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"title\":\"${title}\",\"message\":\"${msg}\",\"notification_id\":\"${nid}\"}" \
      http://supervisor/core/api/services/persistent_notification/create \
      >/dev/null 2>&1 || true
    { set -x; } 2>/dev/null
  fi
}

fetch_tarball() {
  url="https://codeload.github.com/${OWNER}/${REPO}/tar.gz/refs/heads/${BRANCH}"
  out="$1"
  if have curl; then
    echo "[pull] downloading via curl…"
    curl -fsSL "$url" -o "$out"
  elif have wget; then
    echo "[pull] downloading via wget…"
    wget -qO "$out" "$url"
  else
    echo "[pull] ERROR: need curl or wget" >&2
    notify "Repo Pull Failed" "curl/wget not available"
    exit 2
  fi
}

# Version info for version.json, echoed as "SHA TAG" (both single tokens).
#
# PREFERRED source: version_source.json, stamped into the published tree by the
# mirror workflow (.github/workflows/publish.yml). It carries the PRIVATE repo's
# `git describe --tags --always` version ("v0.2.1-10-ge10fc6e") + full commit SHA,
# so the Green mirrors the private version number exactly. Reading it from the
# extracted tarball ($SRCDIR) also drops the GitHub-API round trip (no rate limit,
# works offline-of-github once the tarball is in hand).
#
# FALLBACK (older publish with no stamp, or a legacy pull): the previous behavior
# -- public branch head SHA + latest GitHub Release tag via the API. NOTE $SRCDIR
# is set during extraction (well before this function is called at version time).
fetch_version_info() {
  SHA="unknown"; TAG="unknown"
  VSRC="$SRCDIR/version_source.json"
  if [ -f "$VSRC" ]; then
    SHA=$(sed -n 's/.*"sha"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$VSRC" | head -n1 || echo unknown)
    TAG=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$VSRC" | head -n1 || echo unknown)
  elif have curl; then
    SHA=$(curl -fsSL -H "User-Agent: hass-pull-script" "https://api.github.com/repos/${OWNER}/${REPO}/commits/${BRANCH}" 2>/dev/null \
      | sed -n 's/.*"sha":"\([0-9a-fA-F]\{40\}\)".*/\1/p' | head -n1 || echo unknown)
    TAG=$(curl -fsSL -H "User-Agent: hass-pull-script" "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
      | sed -n 's/.*"tag_name":"\([^"]*\)".*/\1/p' | head -n1 || echo unknown)
  elif have wget; then
    SHA=$(wget -qO- --user-agent="hass-pull-script" "https://api.github.com/repos/${OWNER}/${REPO}/commits/${BRANCH}" 2>/dev/null \
      | sed -n 's/.*"sha":"\([0-9a-fA-F]\{40\}\)".*/\1/p' | head -n1 || echo unknown)
    TAG=$(wget -qO- --user-agent="hass-pull-script" "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
      | sed -n 's/.*"tag_name":"\([^"]*\)".*/\1/p' | head -n1 || echo unknown)
  fi
  [ -n "$SHA" ] || SHA="unknown"
  [ -n "$TAG" ] || TAG="unknown"
  echo "$SHA" "$TAG"
}

# copy tree with delete support if rsync exists
sync_dir() {
  src="$1"; dst="$2"
  shift 2
  if have rsync; then
    mkdir -p "$dst"
    if [ "$DRY_RUN" = "1" ]; then
      echo "[dry-run] rsync --delete preview: $src -> $dst"
      # --dry-run changes nothing; -i itemizes. Removals appear as '*deleting'.
      # shellcheck disable=SC2086
      rsync -a --delete --dry-run -i "$@" "$src/" "$dst/" | sed 's/^/[dry-run]   /'
      return 0
    fi
    echo "[pull] rsync: $src -> $dst"
    # shellcheck disable=SC2086
    rsync -a --delete "$@" "$src/" "$dst/"
  else
    if [ "$DRY_RUN" = "1" ]; then
      echo "[dry-run] rsync not installed -> real pull would cp (no delete); nothing removed under $dst"
      return 0
    fi
    echo "[pull] rsync not found; fallback to cp (no delete)"
    mkdir -p "$dst"
    if [ -d "$src" ]; then
      found=0
      for item in "$src"/* "$src"/.*; do
        base=$(basename "$item")
        case "$base" in .|..) continue;; esac
        [ -e "$item" ] || continue
        found=1
        cp -a "$item" "$dst/" 2>/dev/null || cp -R "$item" "$dst/"
      done
      if [ "$found" -eq 0 ]; then
        echo "[pull] (empty dir) $src"
      fi
      return 0
    fi
    # Source not a directory; nothing to copy in cp-fallback. Do not fail hard.
    return 0
  fi
}

ts() { date -u +"%Y%m%d-%H%M%SZ"; }

# ---- main ----
have tar || { echo "[pull] ERROR: tar not found" >&2; notify "Repo Pull Failed" "tar not found"; exit 2; }

TMPDIR="$(mktemp -d)"; trap 'rm -rf "$TMPDIR"' EXIT

echo "[pull] owner=$OWNER repo=$REPO branch=$BRANCH"
TARBALL="$TMPDIR/repo.tgz"
fetch_tarball "$TARBALL"

echo "[pull] extracting…"
 tar -xzf "$TARBALL" -C "$TMPDIR"
SRCDIR="$TMPDIR/${REPO}-${BRANCH}"
echo "[pull] deep snapshot for packages (depth 3):"
find "$SRCDIR" -maxdepth 3 -type f | sed "s|$SRCDIR/||" | sort | grep -E '^(home-assistant/packages/|esphome/packages/)' || true

# DEBUG: log extracted tree (first two levels)
echo "[pull] tree snapshot under $SRCDIR:"
find "$SRCDIR" -maxdepth 2 -type f | sed "s|$SRCDIR/||" | sort | head -n 120

# ensure targets
mkdir -p "$HA_PKG" "$HA_ESP" "$HA_SCRIPTS" "$HA_BACKUP_DIR"

# configuration.yaml
SRC_CFG="$SRCDIR/$REPO_HA_ROOT/configuration.yaml"
if [ -f "$SRC_CFG" ]; then
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] would overwrite $HA_CFG (backing up the current one first)"
  else
    if [ -f "$HA_CFG" ]; then
      BKP="$HA_BACKUP_DIR/configuration.yaml.$(ts).bak"
      echo "[pull] backup current configuration.yaml -> $BKP"
      cp -f "$HA_CFG" "$BKP"
    fi
    echo "[pull] $REPO_HA_ROOT/configuration.yaml -> $HA_CFG"
    cp -f "$SRC_CFG" "$HA_CFG"
  fi
else
  echo "[pull] WARN: missing in repo: $REPO_HA_ROOT/configuration.yaml (skipping)"
fi

# packages/
SRC_PKG="$SRCDIR/$REPO_HA_ROOT/packages"
if [ -d "$SRC_PKG" ]; then
  echo "[pull] $REPO_HA_ROOT/packages/ -> $HA_PKG/"
  if have rsync; then
    sync_dir "$SRC_PKG" "$HA_PKG" --exclude='.keep'
  else
    sync_dir "$SRC_PKG" "$HA_PKG"
  fi
else
  echo "[pull] WARN: missing in repo: $REPO_HA_ROOT/packages (skipping)"
fi

# scripts/
SRC_SCRIPTS="$SRCDIR/$REPO_HA_ROOT/scripts"
if [ -d "$SRC_SCRIPTS" ]; then
  echo "[pull] $REPO_HA_ROOT/scripts/ -> $HA_SCRIPTS/"
  if have rsync; then
    sync_dir "$SRC_SCRIPTS" "$HA_SCRIPTS" --exclude='.keep'
  else
    sync_dir "$SRC_SCRIPTS" "$HA_SCRIPTS"
  fi
else
  echo "[pull] INFO: no $REPO_HA_ROOT/scripts in repo (skipping)"
fi

# AppDaemon apps. Every home-assistant/appdaemon/<app>/ folder in the repo is
# deployed to $HA_AD_ROOT/<app>/ (NOT under packages/ -- these must not be parsed
# by HA's !include_dir_named). Iterating over every app folder means new apps
# (e.g. repo_pull) deploy and self-update without editing this script. Each
# folder's files (apps.yaml + the app .py files) are copied; the watering_db app
# additionally gets a runtime copy of the canonical docs/db_schema.sql so the
# deployed schema cannot drift from source. NOTE: AppDaemon only re-applies the
# schema / reloads apps on its next restart/reload; the schema is additive
# (CREATE ... IF NOT EXISTS), so a stale-until-restart window is low risk.
SRC_AD_ROOT="$SRCDIR/$REPO_HA_ROOT/appdaemon"
SRC_SCHEMA="$SRCDIR/docs/db_schema.sql"
if [ -d "$SRC_AD_ROOT" ]; then
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] would deploy appdaemon apps (cp, additive -- no deletions) under $HA_AD_ROOT/:"
    for app_dir in "$SRC_AD_ROOT"/*/; do
      [ -d "$app_dir" ] || continue
      echo "[dry-run]   $(basename "$app_dir")"
    done
  else
    for app_dir in "$SRC_AD_ROOT"/*/; do
      [ -d "$app_dir" ] || continue
      app_name=$(basename "$app_dir")
      dst="$HA_AD_ROOT/$app_name"
      echo "[pull] appdaemon/$app_name -> $dst/"
      mkdir -p "$dst"
      for f in "$app_dir"*; do
        [ -f "$f" ] || continue
        cp -f "$f" "$dst/$(basename "$f")"
      done
      echo "[pull] deployed $app_name files: $(find "$dst" -maxdepth 1 -type f | wc -l)"
    done
    # watering_db: refresh the canonical schema alongside the app.
    if [ -d "$HA_AD_DB" ]; then
      if [ -f "$SRC_SCHEMA" ]; then
        echo "[pull] docs/db_schema.sql -> $HA_AD_DB/db_schema.sql"
        cp -f "$SRC_SCHEMA" "$HA_AD_DB/db_schema.sql"
      else
        echo "[pull] WARN: missing in repo: docs/db_schema.sql (schema NOT refreshed)"
      fi
    fi
  fi
else
  echo "[pull] INFO: no $REPO_HA_ROOT/appdaemon in repo (skipping)"
fi

# esphome/ (preserve local secrets/build cache)
SRC_ESP="$SRCDIR/$REPO_ESP_ROOT"
if [ -d "$SRC_ESP" ]; then
  echo "[pull] $REPO_ESP_ROOT/ -> $HA_ESP/ (preserve secrets.yaml)"

  # Always ensure destination subdirs exist
  mkdir -p "$HA_ESP" "$HA_ESP/packages" "$HA_ESP/components"

  # Show what packages the repo has
  if [ -d "$SRC_ESP/packages" ]; then
    echo "[pull] found esphome/packages in repo:"
    find "$SRC_ESP/packages" -maxdepth 1 -type f -print | head -n 20
  else
    echo "[pull] no esphome/packages in repo"
  fi

  # Bulk copy the top-level esphome tree (minus secrets/build)
  if have rsync; then
    sync_dir "$SRC_ESP" "$HA_ESP" --exclude='secrets.yaml' --exclude='.esphome/' --exclude='.gitignore'
  elif [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] rsync not installed; esphome would copy via cp (no delete)"
  else
    # basic recursive copy; will not delete removed files
    for item in "$SRC_ESP"/* "$SRC_ESP"/.*; do
      base=$(basename "$item")
      case "$base" in .|..|.esphome|.gitignore|secrets.yaml) continue;; esac
      [ -e "$item" ] || continue
      cp -a "$item" "$HA_ESP/" 2>/dev/null || cp -R "$item" "$HA_ESP/"
    done
  fi

  # --- FORCE-COPY each YAML in esphome/packages (belt & suspenders, BusyBox-safe) ---
  if [ -d "$SRC_ESP/packages" ] && [ "$DRY_RUN" != "1" ]; then
    for f in "$SRC_ESP"/packages/*.yaml; do
      [ -f "$f" ] || continue
      cp -f "$f" "$HA_ESP/packages/$(basename "$f")"
    done
    echo "[pull] target ESPHome packages count: $(find "$HA_ESP/packages" -maxdepth 1 -type f | wc -l)"
  fi

  # --- COPY esphome/components/ recursively (custom components like victron_ble) ---
  if [ -d "$SRC_ESP/components" ]; then
    if have rsync; then
      if [ "$DRY_RUN" = "1" ]; then
        echo "[dry-run] rsync --delete preview: components -> $HA_ESP/components"
        rsync -a --delete --dry-run -i "$SRC_ESP/components/" "$HA_ESP/components/" | sed 's/^/[dry-run]   /'
      else
        rsync -a --delete "$SRC_ESP/components/" "$HA_ESP/components/"
      fi
    elif [ "$DRY_RUN" = "1" ]; then
      echo "[dry-run] rsync not installed; components would copy via cp (no delete)"
    else
      # create tree, then copy files (BusyBox-safe)
      ( cd "$SRC_ESP/components" && find . -type d -print | while read -r d; do mkdir -p "$HA_ESP/components/$d"; done )
      ( cd "$SRC_ESP/components" && find . -type f -print | while read -r f; do
          cp -f "$SRC_ESP/components/$f" "$HA_ESP/components/$f"
        done )
    fi
    if [ "$DRY_RUN" != "1" ]; then
      echo "[pull] target ESPHome components sample:"
      find "$HA_ESP/components" -maxdepth 2 -type f | head -n 20
    fi
  else
    echo "[pull] no esphome/components in repo"
  fi

else
  echo "[pull] WARN: missing in repo: $REPO_ESP_ROOT (skipping)"
fi

# In dry-run we stop here: nothing was written, and any '*deleting' lines above
# are exactly what a real rsync pull would remove from the Green.
if [ "$DRY_RUN" = "1" ]; then
  echo "[dry-run] complete -- NO changes were made."
  echo "[dry-run] Any '*deleting <path>' lines above are files a real pull WOULD delete."
  echo "[dry-run] If none appear, a real pull would remove nothing."
  exit 0
fi

# ---- versioning: capture tag/sha and write files ----
SHA_TAG=$(fetch_version_info) || SHA_TAG="unknown unknown"
SHA=$(printf '%s\n' "$SHA_TAG" | awk '{print $1}')
TAG=$(printf '%s\n' "$SHA_TAG" | awk '{print $2}')
PULLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Ensure root exists (paranoia)
mkdir -p "$HA_ROOT"

# Write text summary
cat > "$VER_TXT" <<EOF
repo: ${OWNER}/${REPO}
branch: ${BRANCH}
tag: ${TAG}
sha: ${SHA}
pulled_at: ${PULLED_AT}
EOF

# Write JSON summary
printf '{"repo":"%s","branch":"%s","tag":"%s","sha":"%s","pulled_at":"%s"}\n' \
  "${OWNER}/${REPO}" "${BRANCH}" "${TAG}" "${SHA}" "${PULLED_AT}" > "$VER_JSON"

# Verify writes (fail loudly so we see it)
if [ ! -f "$VER_TXT" ] || [ ! -f "$VER_JSON" ]; then
  echo "[pull] ERROR: version files not written: $VER_TXT / $VER_JSON" >&2
  notify "Repo Pull Failed" "Version files not written to $HA_ROOT"
  exit 3
fi

echo "[pull] wrote version files: $VER_TXT, $VER_JSON"

# ---- validate config ----
# The AppDaemon repo_pull app runs this script with PULL_SKIP_VALIDATE=1 because
# it owns validation (Supervisor POST /core/check) and the restart. In that mode
# the file copy is done, version files are written, and we exit 0 without the
# script's own validation/notify so the app is the single source of messaging.
if [ "${PULL_SKIP_VALIDATE:-0}" = "1" ]; then
  echo "[pull] validation skipped (PULL_SKIP_VALIDATE=1); caller owns validate+restart"
  echo "[pull] done. version tag=${TAG} sha=${SHA} at ${PULLED_AT}"
  exit 0
fi

VALID_OK=0
if have ha; then
  echo "[pull] validating via 'ha core check'…"
  if ha core check; then
    VALID_OK=1
  fi
elif have curl && [ -n "${SUPERVISOR_TOKEN-}" ]; then
  echo "[pull] triggering Home Assistant check_config service…"
  curl -fsSL -X POST \
    -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}' \
    http://supervisor/core/api/services/homeassistant/check_config >/dev/null 2>&1 || true
  VALID_OK=1
else
  echo "[pull] WARN: no validation tool available (install 'ha' CLI or use UI check)"
fi

if [ "$VALID_OK" -eq 1 ]; then
  echo "[pull] validation step triggered/ok"
  notify "Repo Pull Succeeded" "Pulled ${OWNER}/${REPO}@${BRANCH} (tag: ${TAG}, sha: ${SHA%%???????????????????????????????????????}). Validation OK/triggered."
else
  echo "[pull] validation failed"
  notify "Repo Pull Failed" "Pulled ${OWNER}/${REPO}@${BRANCH} (tag: ${TAG}, sha: ${SHA}). Validation failed; see logs."
  exit 3
fi

echo "[pull] done. version tag=${TAG} sha=${SHA} at ${PULLED_AT}"
