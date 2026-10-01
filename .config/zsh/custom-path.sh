#!/bin/sh
# Shared by Zsh startup, setup, and diagnostics during the layout migration.
dotfiles_zsh_custom_dir() {
  if [ -d "$HOME/.zshrc_custom" ] && [ ! -L "$HOME/.zshrc_custom" ]; then
    printf '%s\n' "$HOME/.zshrc_custom"
  else
    printf '%s\n' "$HOME/.config/zsh/custom"
  fi
}
