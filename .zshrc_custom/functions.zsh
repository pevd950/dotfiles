# Xcode
openx() {
	        local selected
	        local -a workspaces projects

	        workspaces=( *.xcworkspace(N) )
	        projects=( *.xcodeproj(N) )

	        if (( ${#workspaces[@]} == 1 )); then
	                echo "Opening workspace: ${workspaces[1]}"
	                open "${workspaces[1]}"
	                return
	        elif (( ${#workspaces[@]} > 1 )); then
	                echo "Multiple workspaces found:"
	                select selected in "${workspaces[@]}"; do
	                        [[ -n "$selected" ]] || continue
	                        open "$selected"
	                        return
	                done
	        elif (( ${#projects[@]} == 1 )); then
	                echo "Opening project: ${projects[1]}"
	                open "${projects[1]}"
	                return
	        elif (( ${#projects[@]} > 1 )); then
	                echo "Multiple projects found:"
	                select selected in "${projects[@]}"; do
	                        [[ -n "$selected" ]] || continue
	                        open "$selected"
	                        return
	                done
	        else
	                echo "No Xcode project or workspace found"
	        fi
}

# yadm function to auto-add Claude files
yadm-claude() {
	        echo "Adding Claude files to yadm..."
	        local file
	        local added=0
	        local -a files

	        files=(
	                "$HOME/.claude/CLAUDE.md"
	                "$HOME/.claude/settings.json"
	        )

	        if [[ -d "$HOME/.claude/agents" ]]; then
	                while IFS= read -r -d '' file; do
	                        files+=("$file")
	                done < <(find "$HOME/.claude/agents" -type f -name '*.md' -print0)
	        fi

	        if [[ -d "$HOME/.claude/commands" ]]; then
	                while IFS= read -r -d '' file; do
	                        files+=("$file")
	                done < <(find "$HOME/.claude/commands" -type f -name '*.md' -print0)
	        fi

	        for file in "${files[@]}"; do
	                [[ -f "$file" ]] || continue
	                if yadm add "$file"; then
	                        ((added += 1))
	                fi
	        done

	        echo "Added $added files to yadm"
	        yadm status
}

# turn hidden files on/off in Finder
function hiddenOn() { defaults write com.apple.Finder AppleShowAllFiles YES; }
function hiddenOff() { defaults write com.apple.Finder AppleShowAllFiles NO; }

# myIP address
function myip() {
	        local iface
	        local addr
	        local found=0

	        for iface in ${(z)$(ifconfig -l)}; do
	                addr=$(ipconfig getifaddr "$iface" 2>/dev/null) || continue
	                printf "%-10s %s\n" "$iface" "$addr"
	                found=1
	        done

	        (( found )) || echo "No active connection"
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
