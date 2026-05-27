# Keep this file lightweight: it is sourced by every zsh invocation,
# including non-interactive shells used by SSH remote commands.
typeset -U path PATH

[[ -d "/Applications/Codex.app/Contents/Resources" ]] && path=("/Applications/Codex.app/Contents/Resources" $path)
[[ -d "/opt/homebrew/bin" ]] && path=("/opt/homebrew/bin" $path)
[[ -d "$HOME/.local/bin" ]] && path=("$HOME/.local/bin" $path)
[[ -d "$HOME/.zshrc_custom/bin" ]] && path=("$HOME/.zshrc_custom/bin" $path)

if [[ -z "$CODEX_HOME" ]]; then
        [[ -d "$HOME/.codex-home" ]] && CODEX_HOME="$HOME/.codex-home" || CODEX_HOME="$HOME/.codex"
fi
export CODEX_HOME
export PATH

[[ -f "$HOME/.zshenv.local" ]] && source "$HOME/.zshenv.local"
