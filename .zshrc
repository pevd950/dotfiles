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

# Flutter
export PATH=$PATH:$USER/flutter/bin

# Android
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Export React Editor
export REACT_EDITOR=code

# Docker
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin/"

# go and goproxy setup
export GOPROXY=https://goproxy.githubapp.com/mod,https://proxy.golang.org/,direct
export GOPRIVATE=
export GONOPROXY=
export GONOSUMDB='github.com/github/*'
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Other paths
export MANPATH="/usr/local/man:$MANPATH"
export PATH=/opt/homebrew/bin:$PATH
export PATH=$HOME/.rbenv/bin:$PATH
export SSH_AUTH_SOCK=~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock

# Secrets sourced from 1Password
# YADM_CLASS=$(yadm config local.class)
# if [ "$YADM_CLASS" = "work" ]; then
#    eval "$(op signin --account github)"
#    export GITHUB_TOKEN=$(op item get GITHUB_TOKEN --fields credential)
#    export AZURE_DEVOPS_ACCESS_TOKEN=$(op item get AZURE_DEVOPS_ACCESS_TOKEN --fields credential)
# fi

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
source /Users/pablovalero/.config/op/plugins.sh

source /Users/pablovalero/.config/broot/launcher/bash/br
