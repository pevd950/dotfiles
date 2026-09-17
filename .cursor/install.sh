#!/usr/bin/env bash
# Cloud Agent environment bootstrap for the dotfiles repo.
# Idempotent: installs the validation toolchain and prepares the checks venv.
set -euo pipefail

cd "$(dirname "$0")/.."

export DEBIAN_FRONTEND=noninteractive

# System tools required by scripts/check.sh and the yadm alternates flow.
# Mirrors the "Install validation tools" step in .github/workflows/ci.yml.
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  shellcheck \
  zsh \
  yadm \
  python3-venv

# Create the isolated .venv-checks environment with the checker dependencies.
bash scripts/setup-checks.sh
