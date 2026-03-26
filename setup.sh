#!/usr/bin/env bash

set -euo pipefail

OH_MY_ZSH_INSTALL_URL="https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/1e3abc123f690c9bdd416e8224f1beb47c96f1c7/tools/install.sh"
OH_MY_ZSH_INSTALL_SHA256="ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352"

STARSHIP_INSTALL_URL="https://raw.githubusercontent.com/starship/starship/v1.22.1/install/install.sh"
STARSHIP_INSTALL_SHA256="56da063be2d93348b6181275b235108ad6dd39bc2c2faee053889f57666ac30a"

HOMEBREW_INSTALL_URL="https://raw.githubusercontent.com/Homebrew/install/a5e5c3da45367f1b14512c457728fea75eb18d23/install.sh"
HOMEBREW_INSTALL_SHA256="1c9db64f27d7487ecf74fe3543b96beb1f78039cc92745c3e825a9a7ccefec80"

sha256_file() {
  local file="$1"
  if command -v sha256sum &> /dev/null; then
    sha256sum "$file" | awk '{print $1}'
  else
    shasum -a 256 "$file" | awk '{print $1}'
  fi
}

run_verified_script() {
  local interpreter="$1"
  local url="$2"
  local expected_sha256="$3"
  shift 3

  local tmp_script
  tmp_script="$(mktemp)"
  trap 'rm -f "$tmp_script"' RETURN

  curl -fsSL "$url" -o "$tmp_script"

  local actual_sha256
  actual_sha256="$(sha256_file "$tmp_script")"
  if [ "$actual_sha256" != "$expected_sha256" ]; then
    echo "Checksum verification failed for $url" >&2
    echo "Expected: $expected_sha256" >&2
    echo "Actual:   $actual_sha256" >&2
    return 1
  fi

  "$interpreter" "$tmp_script" "$@"
}

# Define a function to install Oh My Zsh
install_oh_my_zsh() {
  if [ ! -d "$HOME/.oh-my-zsh" ]; then
    run_verified_script /bin/sh "$OH_MY_ZSH_INSTALL_URL" "$OH_MY_ZSH_INSTALL_SHA256"
  fi
}

# Define a function to install Starship
install_starship() {
  if ! command -v starship &> /dev/null; then
    run_verified_script /bin/sh "$STARSHIP_INSTALL_URL" "$STARSHIP_INSTALL_SHA256" -y
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
    run_verified_script /bin/bash "$HOMEBREW_INSTALL_URL" "$HOMEBREW_INSTALL_SHA256"
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
