#!/usr/bin/env bash
# Cloud Agent environment bootstrap for the dotfiles repo.
# Idempotent: installs the validation toolchain and prepares the checks venv.
set -euo pipefail

cd "$(dirname "$0")/.."

export DEBIAN_FRONTEND=noninteractive

need_apt=0
for cmd in shellcheck zsh yadm python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    need_apt=1
    break
  fi
done
if ! python3 -c 'import venv' >/dev/null 2>&1; then
  need_apt=1
fi

if [ "$need_apt" -eq 1 ]; then
  # System tools required by scripts/check.sh and the yadm alternates flow.
  # Mirrors the "Install validation tools" step in .github/workflows/ci.yml.
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    shellcheck \
    zsh \
    yadm \
    python3-venv
else
  echo "Validation toolchain already present; skipping apt-get."
fi

if .venv-checks/bin/python -c 'import yaml, markdown_it' >/dev/null 2>&1; then
  echo "Checks venv already has required modules; skipping setup-checks.sh."
else
  bash scripts/setup-checks.sh
fi
