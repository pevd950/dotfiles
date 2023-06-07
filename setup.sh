#!/usr/bin/env bash

# Define a function to install Oh My Zsh
install_oh_my_zsh() {
  if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
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
  # Install tools
  install_oh_my_zsh
  install_starship
#   install_rbenv
fi
