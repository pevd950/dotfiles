#macOS
alias o="open ."

# cd
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Git
alias gs='git status'
alias gc="git checkout"
alias gcm="git checkout master"
alias gpull="git pull"
alias gpush="git push"
alias gm="git merge"
alias gbranch="git checkout -b"
alias gclone="git clone"
alias gt="gittower ."

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
alias myaliases='code "$ZSH_CUSTOM"/alias.zsh'

# Apps
# MacUpdater
alias macupdater='/Applications/MacUpdater.app/Contents/Resources/macupdater_client'
