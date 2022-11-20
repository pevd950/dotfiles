# #Checking if arm64 or x86
# HOST_ARCH=$(uname -m)

SAVEHIST=20000
HISTSIZE=20000
setopt HIST_FIND_NO_DUPS
setopt HIST_IGNORE_ALL_DUPS

# Exports
# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

#Flutter
export PATH=$PATH:$USER/flutter/bin
#Android
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
#Export React Editor
export REACT_EDITOR=code
#Docker
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin/"
# go and goproxy setup
export GOPROXY=https://goproxy.githubapp.com/mod,https://proxy.golang.org/,direct
export GOPRIVATE=
export GONOPROXY=
export GONOSUMDB='github.com/github/*'
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
# export MANPATH="/usr/local/man:$MANPATH"
export PATH=/opt/homebrew/bin:$PATH
export PATH=$HOME/.rbenv/bin:$PATH

# Secrets sourced from 1Password
# YADM_CLASS=$(yadm config local.class)
# if [ "$YADM_CLASS" = "work" ]; then
#    eval "$(op signin --account github)"
#    export GITHUB_TOKEN=$(op item get GITHUB_TOKEN --fields credential)
#    export AZURE_DEVOPS_ACCESS_TOKEN=$(op item get AZURE_DEVOPS_ACCESS_TOKEN --fields credential)
# fi

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
ZSH_CUSTOM=~/.zshrc_custom/

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
#Disabled plugins
   # git-prompt 

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

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

#arch conditional aliases
# if [ "arm64" = $HOST_ARCH ]; then
#    alias ibrew='arch -x86_64 /usr/local/bin/brew'
#    alias python=/opt/homebrew/bin/python3
# fi

#Host and user in prompt for ssh connections
if [[ -n $SSH_CONNECTION ]]; then
   PROMPT="%{$fg[white]%}%n@%{$fg[green]%}%m%{$reset_color%} ${PROMPT}"
fi

ZSH_DISABLE_COMPFIX="true"
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

