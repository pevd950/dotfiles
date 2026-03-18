#!/usr/bin/env bash

# Define a function to install Oh My Zsh
install_oh_my_zsh() {
  if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)" --unattended
  fi
}

# Define a function to install Starship
install_starship() {
  if ! command -v starship &> /dev/null; then
    curl -fsSL https://starship.rs/install.sh | sh -s -- -y
  fi
}

install_zsh_syntax_highlighting() {
  local plugin_dir="$1"
  local pinned_commit="f1944d8f8b7628f409f90adcf1d40eb6aa797e53"

  if [ -d "$plugin_dir" ]; then
    echo "zsh-syntax-highlighting plugin already installed"
    return
  fi

  echo "Installing zsh-syntax-highlighting plugin at pinned commit..."
  mkdir -p "$(dirname "$plugin_dir")"
  git init -q "$plugin_dir"
  git -C "$plugin_dir" remote add origin https://github.com/zsh-users/zsh-syntax-highlighting.git
  git -C "$plugin_dir" fetch --depth 1 origin "$pinned_commit"
  git -C "$plugin_dir" checkout --detach -q FETCH_HEAD
}

if [[ "$(uname)" == "Darwin" ]]; then
  # Install Homebrew if not present
  if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    echo "Homebrew already installed"
  fi
  
  # Install packages from Brewfile if it exists
  if [ -f "$HOME/.Brewfile" ]; then
    echo "Installing packages from ~/.Brewfile..."
    brew bundle --global
  else
    echo "No ~/.Brewfile found, skipping brew bundle"
  fi

  # Setup Node with nodenv after Brewfile installs it
  if command -v nodenv &> /dev/null; then
    echo "Setting up Node with nodenv..."
    eval "$(nodenv init -)"

    if ! nodenv versions | grep -q "20.17.0"; then
      echo "Installing Node 20.17.0..."
      nodenv install 20.17.0
    else
      echo "Node 20.17.0 already installed"
    fi

    nodenv global 20.17.0
    # Clean up a stale shim left behind by older nodenv runs before rehashing.
    if [ -f "$HOME/.nodenv/shims/.nodenv-shim" ]; then
      rm -f "$HOME/.nodenv/shims/.nodenv-shim"
    fi
    nodenv rehash
    echo "Node $(node -v) is now active"
  fi

  # Install Oh My Zsh and other tools
  install_oh_my_zsh
  install_starship

  # Install Oh My Zsh plugins
  ZSH_HIGHLIGHT_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting"
  install_zsh_syntax_highlighting "$ZSH_HIGHLIGHT_DIR"
  
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

  # Install Oh My Zsh plugins
  ZSH_HIGHLIGHT_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting"
  install_zsh_syntax_highlighting "$ZSH_HIGHLIGHT_DIR"
fi
