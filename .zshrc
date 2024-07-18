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
   source ~/.zshrc_custom/debian-exports.zsh
fi

# go and goproxy setup
export GOPROXY=https://goproxy.githubapp.com/mod,https://proxy.golang.org/,direct
export GOPRIVATE=github.com
export GONOPROXY=
export GONOSUMDB='github.com/github/*'
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

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
   copyfile
   copypath
   dash
   docker
   docker-compose
   encode64
   gh
   git
   golang
   per-directory-history
   helm
   history
   kubectl
   macos
   rails
   ruby
   terraform
   web-search
   zsh-syntax-highlighting
   1password
)
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

# Custom configurations
ZSH_DISABLE_COMPFIX="true"
ZSH_CUSTOM=~/.zshrc_custom
source $ZSH/oh-my-zsh.sh

# Source alias-local.zsh if it exists
if [ -f "${ZSH_CUSTOM}/alias-local.zsh" ]; then
    source "${ZSH_CUSTOM}/alias-local.zsh"
fi

# Source exports-local.zsh if it exists
if [ -f "${ZSH_CUSTOM}/exports-local.zsh" ]; then
    source "${ZSH_CUSTOM}/exports-local.zsh"
fi

# Init starship prompt
eval "$(starship init zsh)"
# Init shadowenv
eval "$(shadowenv init zsh)"  # for zsh

autoload -U +X bashcompinit && bashcompinit

# Source Last OS-specific export files
if [ "$OS" = "macos" ]; then
   [[ /opt/homebrew/bin/kubectl ]] && source <(kubectl completion zsh)
   #Completion for 1Password CLI
   eval "$(op completion zsh)"
   compdef _op op
   # Init ruby env
   eval "$(rbenv init - zsh)"
   # Init node env
   eval "$(nodenv init -)"
   # Init shadoe env
   eval "$(pyenv init -)"
   complete -o nospace -C /opt/homebrew/bin/bit bit
   # iTerm2 integration
   source ~/.iterm2_shell_integration.zsh
   export NVM_DIR="$HOME/.nvm"
   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
   [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion
   export PATH="/opt/homebrew/sbin:$PATH"
   # Enable this for 1Password CLI Plugins
   # source ~/.config/op/plugins.sh
   # source ~/.config/broot/launcher/bash/br
   # source /Users/pablovalero/.config/broot/launcher/bash/br
elif [ "$OS" = "debian" ]; then
fi
