# Xcode
openx() {
        if test -n "$(find . -maxdepth 1 -name '*.xcworkspace' -print -quit)"; then
                echo "Opening workspace"
                open *.xcworkspace
                return
        else
                if test -n "$(find . -maxdepth 1 -name '*.xcodeproj' -print -quit)"; then
                        echo "Opening project"
                        open *.xcodeproj
                        return
                else
                        echo "Nothing found"
                fi
        fi
}

# yadm function to auto-add Claude files
yadm-claude() {
    echo "Adding Claude files to yadm..."
    yadm add ~/.claude/agents/*.md 2>/dev/null
    yadm add ~/.claude/commands/*.md 2>/dev/null
    yadm add ~/.claude/CLAUDE.md 2>/dev/null
    yadm add ~/.claude/settings.json 2>/dev/null
    yadm status
}

# turn hidden files on/off in Finder
function hiddenOn() { defaults write com.apple.Finder AppleShowAllFiles YES; }
function hiddenOff() { defaults write com.apple.Finder AppleShowAllFiles NO; }

# myIP address
function myip() {
        ifconfig lo0 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "lo0       : " $2}'
        ifconfig en0 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "en0 (IPv4): " $2 " " $3 " " $4 " " $5 " " $6}'
        ifconfig en0 | grep 'inet6 ' | sed -e 's/ / /' | awk '{print "en0 (IPv6): " $2 " " $3 " " $4 " " $5 " " $6}'
        ifconfig en1 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "en1 (IPv4): " $2 " " $3 " " $4 " " $5 " " $6}'
        ifconfig en1 | grep 'inet6 ' | sed -e 's/ / /' | awk '{print "en1 (IPv6): " $2 " " $3 " " $4 " " $5 " " $6}'
}

# Show file in quick look
function quick-look() {
        (($# > 0)) && qlmanage -p $* &>/dev/null &
}

# Open man page in preview app
preman() {
        mandoc -T pdf "$(/usr/bin/man -w $@)" | open -fa Preview
}
# Expose kubernetes context for iTerm
iterm2_print_user_vars() {
        KUBECONTEXT=$(
                CTX=$(kubectl config current-context) 2>/dev/null
                if [ $? -eq 0 ]; then echo $CTX; fi
        )
        iterm2_set_user_var kubeContext $KUBECONTEXT
}

# Function to handle Git command suggestions
copilot_git_suggest() {
        gh copilot suggest -t git "$@"
}

# Function to handle GitHub CLI command suggestions
copilot_gh_suggest() {
        gh copilot suggest -t gh "$@"
}

copilot_shell_suggest() {
        gh copilot suggest -t shell "$@"
}

codex() {
        if [ -n "$CODEX_HOME" ]; then
                command codex "$@"
                return
        fi

        if [ "$PWD" = "$HOME" ]; then
                local codex_home="$HOME/.codex-home"
                if [ ! -d "$codex_home" ]; then
                        codex_home="$HOME/.codex"
                fi
                CODEX_HOME="$codex_home" command codex "$@"
        else
                command codex "$@"
        fi
}

# Fun
flip() { echo -n "（╯°□°）╯ ┻━┻" |tee /dev/tty| pbcopy -selection clipboard; }

# shrug() { echo -n "¯\_(ツ)_/¯" |tee /dev/tty| pbcopy -selection clipboard; }
