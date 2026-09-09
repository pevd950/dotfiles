#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

checks_python="${DOTFILES_CHECK_PYTHON:-.venv-checks/bin/python}"
if ! "$checks_python" -c 'import yaml, markdown_it' >/dev/null 2>&1; then
  echo "Run bash scripts/setup-checks.sh first (Python venv support is required)." >&2
  exit 1
fi

bash_files=(
  setup.sh
  scripts/setup-checks.sh
  .config/yadm/bootstrap
  .zshrc_custom/bin/coderabbit
  .zshrc_custom/bin/cr
)

zsh_files=(
  .zshenv
  .zshrc
  .zshrc_custom/alias.zsh
  .zshrc_custom/docker-compose-detection.zsh
  .zshrc_custom/functions.zsh
  .zshrc_custom/macos-exports
  .zshrc_custom/debian-exports
  .zshrc_custom/bin/onepassword-dev-preflight
  scripts/setup-1password-dev.zsh
)

shellcheck "${bash_files[@]}"

for file in "${bash_files[@]}"; do
  bash -n "$file"
done

for file in "${zsh_files[@]}"; do
  zsh -n "$file"
done

"$checks_python" -m unittest discover \
  -s .agents/skills/development/babysit-pr/scripts -p 'test_*.py'

"$checks_python" scripts/check_instructions.py
"$checks_python" -m unittest discover -s scripts -p "test_*.py"
