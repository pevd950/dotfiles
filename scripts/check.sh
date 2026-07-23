#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

bash_files=(
  setup.sh
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

python3 -m unittest discover -s tests -p 'test_*.py'
