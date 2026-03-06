# Keep this file lightweight: it is sourced by every zsh invocation,
# including non-interactive shells used by SSH remote commands.
typeset -U path PATH

[[ -d "/Applications/Codex.app/Contents/Resources" ]] && path=("/Applications/Codex.app/Contents/Resources" $path)
[[ -d "/opt/homebrew/bin" ]] && path=("/opt/homebrew/bin" $path)
[[ -d "$HOME/.local/bin" ]] && path=("$HOME/.local/bin" $path)
[[ -d "$HOME/.zshrc_custom/bin" ]] && path=("$HOME/.zshrc_custom/bin" $path)

export PATH
