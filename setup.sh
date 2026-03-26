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
  local pinned_commit="1d85c692615a25fe2293bdd44b34c217d5d2bf04"
  local repo_url="https://github.com/zsh-users/zsh-syntax-highlighting.git"

  if ! command -v git &> /dev/null; then
    echo "git is required to install zsh-syntax-highlighting" >&2
    return 1
  fi

  if [ -d "$plugin_dir/.git" ]; then
    local current_commit
    current_commit="$(git -C "$plugin_dir" rev-parse HEAD 2>/dev/null || true)"
    if [ "$current_commit" = "$pinned_commit" ]; then
      echo "zsh-syntax-highlighting already pinned at expected commit"
      return 0
    fi
    echo "Re-pinning existing zsh-syntax-highlighting checkout..."
  elif [ -e "$plugin_dir" ]; then
    echo "Replacing existing zsh-syntax-highlighting directory with pinned checkout..."
  else
    echo "Installing zsh-syntax-highlighting plugin at pinned commit..."
  fi

  mkdir -p "$(dirname "$plugin_dir")" || return 1

  local tmp_dir
  tmp_dir="$(mktemp -d "$(dirname "$plugin_dir")/.zsh-syntax-highlighting.XXXXXX")" || return 1
  trap 'rm -rf "$tmp_dir"' RETURN

  git init -q "$tmp_dir" &&
  git -C "$tmp_dir" remote add origin "$repo_url" &&
  git -C "$tmp_dir" fetch --depth 1 origin "$pinned_commit" &&
  git -C "$tmp_dir" checkout --detach -q FETCH_HEAD || return 1

  if [ "$(git -C "$tmp_dir" rev-parse HEAD)" != "$pinned_commit" ]; then
    echo "Expected zsh-syntax-highlighting commit $pinned_commit after fetch, got $(git -C "$tmp_dir" rev-parse HEAD)" >&2
    return 1
  fi

  local backup_dir=""
  if [ -e "$plugin_dir" ]; then
    backup_dir="$(dirname "$plugin_dir")/.zsh-syntax-highlighting-backup.$(basename "$plugin_dir").$$"
    rm -rf "$backup_dir"
    mv "$plugin_dir" "$backup_dir" || return 1
  fi

  if ! mv "$tmp_dir" "$plugin_dir"; then
    if [ -n "$backup_dir" ] && [ -e "$backup_dir" ]; then
      command mv "$backup_dir" "$plugin_dir" || true
    fi
    return 1
  fi

  if [ -n "$backup_dir" ] && [ -e "$backup_dir" ]; then
    rm -rf "$backup_dir"
  fi
  trap - RETURN
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
  install_zsh_syntax_highlighting "$ZSH_HIGHLIGHT_DIR" || exit 1
  
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
  install_zsh_syntax_highlighting "$ZSH_HIGHLIGHT_DIR" || exit 1
fi
