#macOS
alias o="open ."

# cd
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Git
alias gs='git status'
alias gc="git checkout"
alias gcm="git checkout main"
alias gpull="git pull"
alias gpush="git push"
alias gm="git merge"
alias gcb="git checkout -b"
alias gclone="git clone"
alias gt="gittower ."
alias gcr="git rebase --continue"

# GitHub
# gh alias set --shell startcs 'gh cs code -c $(gh cs list --json "name" | jq -r ".[].name" | grep -i "$1" -m 1)'
# gh alias set --shell stopcs 'gh cs stop -c $(gh cs list --json "name" | jq -r ".[].name" | grep -i "$1" -m 1)'

# YADM
alias ys="yadm status"
alias ypull="yadm pull"
alias ypush="yadm push"
alias yadd="yadm add"

# Editor
alias zshrc="code ~/.zshrc"
alias nvzshrc='nvim ~/.zshrc'
alias nvaliases='nvim "$ZSH_CUSTOM"/alias.zsh'
alias myaliases='code "$ZSH_CUSTOM"/alias.zsh'
alias myfunctions='code "$ZSH_CUSTOM"/functions.zsh'
alias myplugins='code "$ZSH_CUSTOM"/plugins.zsh'
alias myzshrc='code "$ZSH_CUSTOM"'

# Command Overrides
alias cat='bat --paging=never'
alias ls='exa --icons -s=Name'
alias nv='nvim'
alias ql='quick-look'
alias pman='preman'

## Apps

# MacUpdater
alias macupdater='/Applications/MacUpdater.app/Contents/Resources/macupdater_client'

# VSCode
alias vsc='code .'
alias coden='code --new-window'
