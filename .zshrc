# #Checking if arm64 or x86
# HOST_ARCH=$(uname -m)

# History settings
SAVEHIST=50000
HISTSIZE=50000
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS

# Paths and environment variables
# Oh-my-zsh path
export ZSH="$HOME/.oh-my-zsh"

if [[ "$(uname)" == "Darwin" ]]; then
  # macOS-specific configurations
  OS="macos"
  source ~/.zshrc_custom/macos-exports.zsh
elif [[ "$(uname)" == "Linux" ]] && [ -e "/etc/debian_version" ]; then
  # Debian-based Linux configurations
  OS="debian"
  source ~/.zshrc_custom/debian_exports.zsh
fi

# if macOS


# go and goproxy setup
export GOPROXY=https://goproxy.githubapp.com/mod,https://proxy.golang.org/,direct
export GOPRIVATE=
export GONOPROXY=
export GONOSUMDB='github.com/github/*'
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Other paths
export MANPATH="/usr/local/man:$MANPATH"
export PATH=$HOME/.rbenv/bin:$PATH

# Set name of the theme to load --- if set to "random", it will
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
   aliases
   colored-man-pages
   common-aliases
   copyfile
   copypath
   dash
   docker
   docker-compose
   encode64
   gh
   git
   git-open
   golang
   per-directory-history
   helm
   history
   kubectl
   macos
   rails
   ruby
   tmux
   web-search
   zsh-syntax-highlighting
   1password
)

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

# Custom configurations
ZSH_DISABLE_COMPFIX="true"
ZSH_CUSTOM=~/.zshrc_custom/
source $ZSH/oh-my-zsh.sh
source $ZSH_CUSTOM/alias-local.zsh
source $ZSH_CUSTOM/exports-local.zsh

# iTerm2 integration
source ~/.iterm2_shell_integration.zsh

[[ /opt/homebrew/bin/kubectl ]] && source <(kubectl completion zsh)

#Completion for 1Password CLI
eval "$(op completion zsh)"; compdef _op op
# Init ruby env
eval "$(rbenv init - zsh)"
# Init node env
eval "$(nodenv init -)"
# Init starship prompt
eval "$(starship init zsh)"

autoload -U +X bashcompinit && bashcompinit


complete -o nospace -C /opt/homebrew/bin/bit bit

# Source Last OS-specific export files
if [ "$OS" = "macos" ]; then
  source ~/.config/op/plugins.sh
  source ~/.config/broot/launcher/bash/br
elif [ "$OS" = "debian" ]; then
#   source ~/.zsh_exports/debian_exports.zsh
fi


source /Users/pablovalero/.config/broot/launcher/bash/br
