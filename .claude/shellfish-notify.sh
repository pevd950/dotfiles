#!/bin/sh
# shellfish-notify — Secure ShellFish hook helper for agentic coding hooks.
#
# Reads a hook JSON payload on stdin and forwards it to ShellFish through an
# OSC 6 sequence on the controlling terminal. The notification appears on
# whichever device is currently displaying the terminal that owns this
# session, and is silent when the ShellFish app is already in the foreground.
#
# The Shell Integration installer can wire this up for you — re-run Install
# from the app and pick "Install" when prompted. To do it by hand, add a
# hook to ~/.claude/settings.json using the absolute path (Claude Code does
# not expand ~ or $HOME inside hook commands):
#
#   "hooks": {
#     "Notification": [{"hooks":[{"type":"command",
#       "command":"/Users/you/.claude/shellfish-notify.sh claude"}]}],
#     "Stop": [{"hooks":[{"type":"command",
#       "command":"/Users/you/.claude/shellfish-notify.sh claude"}]}]
#   }
#
# Codex CLI and OpenCode use equivalent hook syntax — pass the matching tool
# name as the first argument (codex, opencode, …).

tool="${1:-agent}"
hook=$(cat)

tool_b64=$(printf '%s' "$tool" | base64 | tr -d '\n')
hook_b64=$(printf '%s' "$hook" | base64 | tr -d '\n')
osc="6;codingagenthook://?ver=2&tool=${tool_b64}&hook=${hook_b64}"

# write directly to the controlling terminal — stdout is a pipe to the agent
# process, which would swallow the escape. /dev/tty resolves to the tmux pty
# (so passthrough is unwrapped properly) when inside tmux; falls back to the
# inherited SSH login pty for the rare detached-controlling-tty case.
if [ -n "$TMUX" ]; then
  printf "\033Ptmux;\033\033]%s\a\033\\\\" "$osc" > /dev/tty 2>/dev/null || true
else
  printf "\033]%s\a" "$osc" > /dev/tty 2>/dev/null \
    || { [ -n "$SSH_TTY" ] && printf "\033]%s\a" "$osc" > "$SSH_TTY" 2>/dev/null; } \
    || true
fi
