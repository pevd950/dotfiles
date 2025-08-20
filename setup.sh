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
  # Install Homebrew if not present
  if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    echo "Homebrew already installed"
  fi
  
  # Install tools via Homebrew (brew handles idempotency)
  echo "Installing/updating brew packages..."
  brew install --cask 1password-cli
  brew install nodenv pyenv
  
  # Install Oh My Zsh and other tools
  install_oh_my_zsh
  install_starship
  install_rbenv
  
  # Install packages from Brewfile if it exists
  if [ -f "$HOME/Brewfile" ]; then
    echo "Installing packages from Brewfile..."
    brew bundle --global
  else
    echo "No Brewfile found, skipping brew bundle"
  fi
  
  # Install Oh My Zsh plugins
  ZSH_HIGHLIGHT_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting"
  if [ ! -d "$ZSH_HIGHLIGHT_DIR" ]; then
    echo "Installing zsh-syntax-highlighting plugin..."
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_HIGHLIGHT_DIR"
  else
    echo "zsh-syntax-highlighting plugin already installed"
  fi
  
  # Install iTerm2 shell integration
  if [ ! -f ~/.iterm2_shell_integration.zsh ]; then
    echo "Installing iTerm2 shell integration..."
    curl -L https://iterm2.com/shell_integration/zsh \
      -o ~/.iterm2_shell_integration.zsh
  else
    echo "iTerm2 shell integration already installed"
  fi
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
