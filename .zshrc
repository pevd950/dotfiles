# Zsh discovers this entry point in $HOME. Keep the configuration together.
[[ -r "$HOME/.config/zsh/zshrc" ]] && source "$HOME/.config/zsh/zshrc"

# >>> grok installer >>>
# Only on hosts where Grok is installed.
if [[ -d "$HOME/.grok" ]]; then
  export PATH="$HOME/.grok/bin:$PATH"
  fpath=("$HOME/.grok/completions/zsh" $fpath)
  autoload -Uz compinit && compinit -C
fi
# <<< grok installer <<<

