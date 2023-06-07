#!/usr/bin/env bash

# Define a function to install Oh My Zsh
install_oh_my_zsh() {
  if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)" --unattended
  fi
}

# Define a function to install Starship
install_starship() {
  curl -fsSL https://starship.rs/install.sh | sh -s -- -y
}

# Define a function to install rbenv
install_rbenv() {
  if ! command -v rbenv &> /dev/null; then
    if [[ "$(uname)" == "Darwin" ]]; then
      brew install rbenv
    elif [[ "$(uname)" == "Linux" ]]; then
      sudo apt update
      sudo apt install -y rbenv
    fi
  fi
}

if [[ "$(uname)" == "Darwin" ]]; then
  # Install Homebrew
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Install tools
  install_oh_my_zsh
  install_starship
  install_rbenv
elif [[ "$(uname)" == "Linux" ]]; then
# TODO: This should be shared
  # Install tools
  install_starship
  install_oh_my_zsh
  # Get the directory of the current script
  SCRIPT_DIR="$(dirname "$0")"

  # Install Oh My Zsh plugins
  mkdir -p "${SCRIPT_DIR}/.zshrc_custom/plugins"  # make sure the target directory exists
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "${SCRIPT_DIR}/.zshrc_custom/plugins/zsh-syntax-highlighting"

  # Copy .zshrc and .zshrc_custom/ to $HOME
  cp "${SCRIPT_DIR}/.zshrc" ~/
  cp -r "${SCRIPT_DIR}/.zshrc_custom/" ~/
fi
