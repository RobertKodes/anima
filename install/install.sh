#!/usr/bin/env bash
# Anima installer — macOS, Linux, WSL
# Usage: curl -fsSL https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.sh | bash
set -euo pipefail

ANIMA_REPO="${ANIMA_REPO:-https://github.com/RobertKodes/anima.git}"
ANIMA_BRANCH="${ANIMA_BRANCH:-master}"
ANIMA_HOME="${ANIMA_HOME:-$HOME/.anima}"
ANIMA_VENV="${ANIMA_VENV:-$ANIMA_HOME/.venv}"
NO_ONBOARD=0
NO_PATH=0
DRY_RUN=0

log() { printf '\033[0;36m[anima]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[anima]\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[anima]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Anima installer

Usage:
  curl -fsSL .../install/install.sh | bash
  curl -fsSL .../install/install.sh | bash -s -- [options]

Options:
  --no-onboard    Install only; skip anima onboard
  --no-path       Do not update shell PATH
  --dry-run       Show planned steps without changing the system
  -h, --help      Show this help

Environment:
  ANIMA_HOME      Data + venv root (default: ~/.anima)
  ANIMA_REPO      Git repo URL
  ANIMA_BRANCH    Git branch (default: master)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-onboard) NO_ONBOARD=1; shift ;;
    --no-path) NO_PATH=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1 (try --help)" ;;
  esac
done

find_python() {
  local candidates=(python3.12 python3.11 python3.10 python3 python)
  local cmd
  for cmd in "${candidates[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

add_path_hint() {
  local bin="$ANIMA_VENV/bin"
  if [[ "$NO_PATH" -eq 1 ]]; then
    warn "Add to PATH manually: export PATH=\"$bin:\$PATH\""
    return
  fi
  local line="export PATH=\"$bin:\$PATH\""
  for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [[ -f "$rc" ]] && ! grep -Fq "$bin" "$rc" 2>/dev/null; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[dry-run] would append PATH to $rc"
      else
        printf '\n# Added by Anima installer\n%s\n' "$line" >>"$rc"
        log "Updated $rc"
      fi
    fi
  done
  export PATH="$bin:$PATH"
}

anima_pip_source() {
  if [[ -n "${ANIMA_PIP_URL:-}" ]]; then
    echo "$ANIMA_PIP_URL"
    return
  fi
  local repo="${ANIMA_REPO%.git}"
  if [[ "$repo" =~ github\.com/([^/]+/[^/]+)$ ]]; then
    echo "https://github.com/${BASH_REMATCH[1]}/archive/refs/heads/${ANIMA_BRANCH}.zip"
    return
  fi
  echo "git+${ANIMA_REPO}@${ANIMA_BRANCH}"
}

install_anima_package() {
  local source
  source="$(anima_pip_source)"
  log "Installing Anima from $source ..."
  if python -m pip install "$source"; then
    return 0
  fi
  if [[ "$source" != git+* ]]; then
    warn "Zip install failed; retrying via git (requires git)..."
    python -m pip install "git+${ANIMA_REPO}@${ANIMA_BRANCH}" && return 0
  fi
  fail "pip install failed. If git errors persist, install git or set ANIMA_PIP_URL to a release zip."
}

PYTHON="$(find_python || true)"
[[ -n "$PYTHON" ]] || fail "Python 3.10+ is required. Install from https://www.python.org/downloads/"

log "Python: $($PYTHON --version)"
log "Install root: $ANIMA_HOME"
log "Virtual env: $ANIMA_VENV"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "[dry-run] would create venv and pip install $(anima_pip_source)"
  [[ "$NO_ONBOARD" -eq 1 ]] || log "[dry-run] would run: anima onboard --yes --launch"
  exit 0
fi

mkdir -p "$ANIMA_HOME"
if [[ ! -d "$ANIMA_VENV" ]]; then
  log "Creating virtual environment..."
  "$PYTHON" -m venv "$ANIMA_VENV"
fi

# shellcheck disable=SC1091
source "$ANIMA_VENV/bin/activate"
python -m pip install --upgrade pip wheel >/dev/null
install_anima_package

add_path_hint

if [[ "$NO_ONBOARD" -eq 1 ]]; then
  log "Skipping onboard (--no-onboard)."
else
  log "Running onboard..."
  anima onboard --yes --launch
fi

cat <<EOF

Anima is installed.

  anima              graphical CLI
  anima doctor       health check
  anima onboard      change brain / repair setup

Data: $ANIMA_HOME
EOF
