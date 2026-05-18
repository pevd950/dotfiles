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
  .zshrc_custom/functions.zsh
  .zshrc_custom/macos-exports
  .zshrc_custom/debian-exports
)

shellcheck "${bash_files[@]}"
bash -n "${bash_files[@]}"
zsh -n "${zsh_files[@]}"
