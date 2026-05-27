# Xcode
if [[ "$(uname)" == "Darwin" ]]; then
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
fi

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
if [[ "$(uname)" == "Darwin" ]]; then
        function hiddenOn() { defaults write com.apple.Finder AppleShowAllFiles YES; }
        function hiddenOff() { defaults write com.apple.Finder AppleShowAllFiles NO; }
fi

# myIP address
function myip() {
	        local iface
	        local addr
	        local found=0

	        if [[ "$(uname)" == "Darwin" ]]; then
	                for iface in ${(z)$(ifconfig -l)}; do
	                        addr=$(ipconfig getifaddr "$iface" 2>/dev/null) || continue
	                        printf "%-10s %s\n" "$iface" "$addr"
	                        found=1
	                done
	        elif command -v ip >/dev/null 2>&1; then
	                while read -r _ iface _ addr _; do
	                        printf "%-10s %s\n" "${iface%:}" "${addr%/*}"
	                        found=1
	                done < <(ip -o -4 addr show scope global)
	        fi

	        (( found )) || echo "No active connection"
}

# Show file in quick look
if [[ "$(uname)" == "Darwin" ]]; then
        function quick-look() {
                (($# > 0)) && qlmanage -p "$@" &>/dev/null &
        }
fi

# Open man page in preview app
if [[ "$(uname)" == "Darwin" ]]; then
        preman() {
                mandoc -T pdf "$(/usr/bin/man -w "$@")" | open -fa Preview
        }
fi
# Run GitHub Copilot suggestions only after invocation-time availability checks.
_gh_copilot_suggest() {
        if ! command -v gh >/dev/null 2>&1; then
                print -u2 "gh is required for Copilot suggestions."
                return 127
        fi
        if ! gh copilot --help >/dev/null 2>&1; then
                print -u2 "GitHub CLI Copilot is unavailable. Install it with: gh extension install github/gh-copilot"
                return 127
        fi
        gh copilot suggest "$@"
}

# Suggest a shell command with GitHub Copilot.
copilot_what-the-shell() {
        _gh_copilot_suggest -t shell "$@"
}

# Function to handle Git command suggestions
copilot_git_suggest() {
        _gh_copilot_suggest -t git "$@"
}

# Function to handle GitHub CLI command suggestions
copilot_gh_suggest() {
        _gh_copilot_suggest -t gh "$@"
}

# Suggest a shell command with GitHub Copilot.
copilot_shell_suggest() {
        _gh_copilot_suggest -t shell "$@"
}

# Fun
flip() {
        if command -v pbcopy >/dev/null 2>&1; then
                echo -n "（╯°□°）╯ ┻━┻" | tee /dev/tty | pbcopy
        else
                echo -n "（╯°□°）╯ ┻━┻"
        fi
}

# shrug() { echo -n "¯\_(ツ)_/¯" |tee /dev/tty| pbcopy -selection clipboard; }
