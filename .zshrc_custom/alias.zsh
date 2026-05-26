if [[ "$(uname)" == "Darwin" ]]; then
  alias o="open ."
fi

# Search through your command history and print the top 10 commands
alias history-stat="history 0 | awk '{print \$2}' | sort | uniq -c | sort -n -r | head"

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
if command -v gittower >/dev/null 2>&1; then
  alias gt="gittower ."
fi
alias gcr="git rebase --continue"

# Docker
alias dcu="docker-compose up"
alias dcd="docker-compose down"
alias dcb="docker-compose build"
alias dcub="docker-compose up --build"

# yadm
alias yc='yadm-claude'

# GitHub
# gh alias set --shell startcs 'gh cs code -c $(gh cs list --json "name" | jq -r ".[].name" | grep -i "$1" -m 1)'
# gh alias set --shell stopcs 'gh cs stop -c $(gh cs list --json "name" | jq -r ".[].name" | grep -i "$1" -m 1)'

# YADM
alias ys="yadm status"
alias ypull="yadm pull"
alias ypush="yadm push"
alias yadd="yadm add"

# Editor
if command -v code >/dev/null 2>&1; then
  alias zshrc="code ~/.zshrc"
  alias mystarship='code ~/.config/starship.toml'
  alias myaliases='code "$ZSH_CUSTOM"/alias.zsh'
  alias myfunctions='code "$ZSH_CUSTOM"/functions.zsh'
  alias myplugins='code "$ZSH_CUSTOM"/plugins.zsh'
  alias myzshrc='code "$ZSH_CUSTOM"'
  alias vsc='code .'
  alias coden='code --new-window'
fi
alias nvzshrc='nvim ~/.zshrc'
alias nvaliases='nvim "$ZSH_CUSTOM"/alias.zsh'
alias nvstarship='nvim ~/.config/starship.toml'

# Command Overrides
if command -v bat >/dev/null 2>&1; then
  alias bcat='bat --paging=never'
elif command -v batcat >/dev/null 2>&1; then
  alias bcat='batcat --paging=never'
fi
if command -v eza >/dev/null 2>&1; then
  alias dir='eza --icons -s=Name'
elif command -v exa >/dev/null 2>&1; then
  alias dir='exa --icons -s=Name'
fi
alias nv='nvim'
if [[ "$(uname)" == "Darwin" ]]; then
  alias ql='quick-look'
  alias pman='preman'
fi

# Apps

# MacUpdater
if [[ "$(uname)" == "Darwin" && -x "/Applications/MacUpdater.app/Contents/Resources/macupdater_client" ]]; then
  alias macupdater='/Applications/MacUpdater.app/Contents/Resources/macupdater_client'
fi

# Copilot CLI (lazy wrappers avoid running gh during shell startup)
if command -v copilot_what-the-shell >/dev/null 2>&1; then
  alias wts='copilot_what-the-shell'
fi
if command -v copilot_shell_suggest >/dev/null 2>&1; then
  alias '??'='copilot_shell_suggest'
fi
if command -v copilot_git_suggest >/dev/null 2>&1; then
  alias "git?"='copilot_git_suggest'
fi
if command -v copilot_gh_suggest >/dev/null 2>&1; then
  alias 'gh?'='copilot_gh_suggest'
fi

# Fun
if command -v pbcopy >/dev/null 2>&1; then
  alias shrug="echo '¯\_(ツ)_/¯' | pbcopy"
else
  alias shrug="echo '¯\_(ツ)_/¯'"
fi
