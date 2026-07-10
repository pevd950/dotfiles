# #Checking if arm64 or x86
HOST_ARCH=$(uname -m)

# History settings
SAVEHIST=50000
HISTSIZE=50000
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS
typeset -U path PATH

# Paths and environment variables
# Oh-my-zsh path
export ZSH="$HOME/.oh-my-zsh"
ZSH_CUSTOM="$HOME/.zshrc_custom"
[[ -r "$ZSH_CUSTOM/docker-compose-detection.zsh" ]] && source "$ZSH_CUSTOM/docker-compose-detection.zsh"

if [[ -d "$HOME/.local/bin" ]]; then
   path=("$HOME/.local/bin" $path)
fi

if [[ "$(uname)" == "Darwin" ]]; then
   # macOS-specific configurations
   OS="macos"
   [[ -r "$ZSH_CUSTOM/macos-exports" ]] && source "$ZSH_CUSTOM/macos-exports"
elif [[ "$(uname)" == "Linux" ]] && [ -e "/etc/debian_version" ]; then
   # Debian-based Linux configurations
   OS="debian"
   [[ -r "$ZSH_CUSTOM/debian-exports" ]] && source "$ZSH_CUSTOM/debian-exports"
else
   OS="unknown"
fi

# go module auth / proxy setup
# Use the public Go proxy for public modules and bypass it only for personal private modules.
export GOPROXY=https://proxy.golang.org,direct
export GOPRIVATE='github.com/pevd950/*'
unset GONOPROXY
unset GONOSUMDB
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Starship handles the prompt, so skip OMZ theme loading.
ZSH_THEME=""

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
   aliases
   colored-man-pages
   docker
   encode64
   gh
   git
   golang
   per-directory-history
   history
   terraform
   # web-search
   zsh-syntax-highlighting
)

if command -v docker-compose >/dev/null 2>&1 \
   || { whence -w has_docker_compose_cli_plugin >/dev/null 2>&1 && has_docker_compose_cli_plugin; }; then
   plugins+=(docker-compose)
fi

if [[ "$OS" == "macos" ]]; then
   plugins+=(
      copyfile
      copypath
      # kubectl
      macos
      # 1password  # runs `op` on every shell start, triggering macOS app-data
      # prompts at app launch; cached completion in $ZSH_CUSTOM/completions/_op
      # instead (regenerate after op upgrades: op completion zsh > $ZSH_CUSTOM/completions/_op)
   )
fi
#Disabled plugins
# git-prompt
# git-open

# User configuration
export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
if [[ -n $SSH_CONNECTION ]]; then
   export EDITOR='vim'
else
   export EDITOR='nvim'
fi

#Host and user in prompt for ssh connections
if [[ -n $SSH_CONNECTION ]]; then
   PROMPT="%{$fg[white]%}%n@%{$fg[green]%}%m%{$reset_color%} ${PROMPT}"
fi

# Cached completions (e.g. _op) so tools don't run at startup; must be on
# fpath before oh-my-zsh's compinit.
[[ -d "$ZSH_CUSTOM/completions" ]] && fpath=("$ZSH_CUSTOM/completions" $fpath)

# Custom configurations
if [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
   source "$ZSH/oh-my-zsh.sh"
else
   echo "Oh My Zsh not found at $ZSH; skipping plugin loading."
fi

# Source alias-local.zsh if it exists
if [ -f "${ZSH_CUSTOM}/alias-local.zsh" ]; then
    source "${ZSH_CUSTOM}/alias-local.zsh"
fi

# Source exports-local.zsh if it exists
if [ -f "${ZSH_CUSTOM}/exports-local.zsh" ]; then
    source "${ZSH_CUSTOM}/exports-local.zsh"
fi

# Keep wrapper scripts ahead of ~/.local/bin even if local overrides prepend it.
if [[ -d "${ZSH_CUSTOM}/bin" ]]; then
   path=("${ZSH_CUSTOM}/bin" $path)
fi

# Init starship prompt when the terminal supports it.
if [[ "${TERM:-}" != "dumb" ]] && command -v starship >/dev/null 2>&1; then
   eval "$(starship init zsh)"
fi
# Init shadowenv
# eval "$(shadowenv init zsh)"  # for zsh

autoload -U +X bashcompinit && bashcompinit

# Source Last OS-specific export files
if [ "$OS" = "macos" ]; then
   # Skip eager kubectl/op completion generation; run tool-specific completion setup manually when needed.
   # Keep shims on PATH for project commands; lazy-load manager shell integration on first direct use.
   if command -v rbenv >/dev/null 2>&1; then
      [[ -d "$HOME/.rbenv/shims" ]] && path=("$HOME/.rbenv/shims" $path)
      _lazy_init_rbenv() {
         unset -f rbenv _lazy_init_rbenv
         eval "$(command rbenv init - zsh)"
      }
      rbenv() {
         _lazy_init_rbenv
         rbenv "$@"
      }
   fi
   if command -v nodenv >/dev/null 2>&1; then
      [[ -d "$HOME/.nodenv/shims" ]] && path=("$HOME/.nodenv/shims" $path)
      _lazy_init_nodenv() {
         unset -f nodenv _lazy_init_nodenv
         eval "$(command nodenv init -)"
      }
      nodenv() {
         _lazy_init_nodenv
         nodenv "$@"
      }
   fi
   if command -v pyenv >/dev/null 2>&1; then
      [[ -d "$HOME/.pyenv/shims" ]] && path=("$HOME/.pyenv/shims" $path)
      _lazy_init_pyenv() {
         unset -f pyenv _lazy_init_pyenv
         eval "$(command pyenv init - --no-rehash)"
      }
      pyenv() {
         _lazy_init_pyenv
         pyenv "$@"
      }
   fi
   if command -v bit >/dev/null 2>&1; then
      complete -o nospace -C "$(command -v bit)" bit
   fi
   # NVM - commented out in favor of nodenv
   # export NVM_DIR="$HOME/.nvm"
   # [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
   # [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion
   # 1Password CLI shell plugin aliases. Keep this conditional and avoid
   # global aliases unless a plugin is intentionally configured.
   if [[ -r "$HOME/.config/op/plugins.sh" ]]; then
      source "$HOME/.config/op/plugins.sh"
   fi
   # source ~/.config/broot/launcher/bash/br
   # source /Users/pablovalero/.config/broot/launcher/bash/br
elif [ "$OS" = "debian" ]; then
fi

if [[ "$TERM_PROGRAM" == "kiro" ]] && command -v kiro >/dev/null 2>&1; then
   . "$(kiro --locate-shell-integration-path zsh)"
fi

if [[ -e "$HOME/.shellfishrc" ]]; then
   source "$HOME/.shellfishrc"
fi

# Matter CLI
[[ -d "$HOME/.matter/bin" ]] && path=("$HOME/.matter/bin" $path)
