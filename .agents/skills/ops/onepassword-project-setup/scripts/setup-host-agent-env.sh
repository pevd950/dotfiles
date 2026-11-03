#!/usr/bin/env bash
# Install the shared-keys renderer on this host: a refresh script, a scheduled job (launchd on macOS,
# a systemd user timer on Linux), a reference template stub and the shell loader in ~/.zshenv.local.
# Idempotent. Never creates the service account and never prints a secret.
# Usage: setup-host-agent-env.sh --alias HOST [--token-file PATH] [--label LABEL] [--interval SECONDS]
set -euo pipefail
alias="" token="" label="local.refresh-agent-env" interval=21600
while [ $# -gt 0 ]; do case "$1" in
  --alias) alias="$2"; shift 2;; --token-file) token="$2"; shift 2;;
  --label) label="$2"; shift 2;; --interval) interval="$2"; shift 2;;
  *) echo "unknown argument: $1" >&2; exit 2;; esac; done
[ -n "$alias" ] || { echo "usage: $0 --alias HOST [--token-file PATH] [--label LABEL]" >&2; exit 2; }
token="${token:-$HOME/.config/op/sa/$alias-agents.token}"
envdir="$HOME/.config/op/env"; tpl="$envdir/$alias-agent.env.tpl"; out="$envdir/$alias-agent.env"
bin="$HOME/.local/bin/refresh-agent-env"
umask 077; mkdir -p "$envdir" "$HOME/.local/bin"; chmod 700 "$envdir"

cat > "$bin" <<EOF
#!/bin/zsh
# Render $out from its template with the token in $token. Safe to rerun.
set -euo pipefail
tpl="$tpl"; out="$out"; tok="$token"
[[ -r "\$tok" ]] || { echo "refresh-agent-env: missing \$tok, keeping previous file" >&2; exit 1; }
export OP_SERVICE_ACCOUNT_TOKEN="\$(<"\$tok")"
umask 077; tmp="\$(mktemp "\$out.XXXXXX")"
op inject -i "\$tpl" -o "\$tmp" --force >/dev/null
if grep -q 'op://' "\$tmp"; then rm -f "\$tmp"; echo "refresh-agent-env: unresolved reference, keeping previous file" >&2; exit 1; fi
mv -f "\$tmp" "\$out"; chmod 600 "\$out"; echo "rendered \$out (\$(grep -c '=' "\$out") vars)"
EOF
chmod 700 "$bin"

if [ ! -e "$tpl" ]; then cat > "$tpl" <<EOF
# $alias shared agent and shell secrets, as 1Password references (no values).
# One NAME=op://<vault>/<item-id>/<field> line per variable, item title in a comment below it.
# Reference item IDs so renames never break this host. Edit here, then run refresh-agent-env.
EOF
  echo "created template stub $tpl"; fi
chmod 600 "$tpl"

path="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
case "$(uname -s)" in
  Darwin)
    plist="$HOME/Library/LaunchAgents/$label.plist"; mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
    cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array><string>$bin</string></array>
  <key>EnvironmentVariables</key><dict><key>HOME</key><string>$HOME</string><key>PATH</key><string>$path</string></dict>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>$interval</integer>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/refresh-agent-env.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/refresh-agent-env.log</string>
</dict></plist>
EOF
    plutil -lint "$plist" >/dev/null
    launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist"; echo "launchd job $label loaded";;
  Linux)
    u="$HOME/.config/systemd/user"; mkdir -p "$u"
    printf '[Unit]\nDescription=Render shared agent secrets\n\n[Service]\nType=oneshot\nEnvironment=PATH=%s\nExecStart=%s\n' "$path" "$bin" > "$u/refresh-agent-env.service"
    printf '[Unit]\nDescription=Refresh shared agent secrets\n\n[Timer]\nOnBootSec=2min\nOnUnitActiveSec=%ss\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n' "$interval" > "$u/refresh-agent-env.timer"
    systemctl --user daemon-reload; systemctl --user enable --now refresh-agent-env.timer; echo "systemd timer enabled";;
esac

zl="$HOME/.zshenv.local"; touch "$zl"; chmod 600 "$zl"
if ! grep -q 'refresh-agent-env' "$zl"; then cat >> "$zl" <<EOF

# Shared agent and shell secrets: edit the 1Password references in
# $tpl, then run refresh-agent-env. A scheduled job renders them;
# nothing here calls 1Password, so shells and SSH commands never prompt.
_agent_env="$out"
if [[ ! -r "\$_agent_env" || -n "\$(find "\$_agent_env" -mtime +1 2>/dev/null)" ]] && [[ -x "\$HOME/.local/bin/refresh-agent-env" ]]; then
  "\$HOME/.local/bin/refresh-agent-env" >/dev/null 2>&1 || true   # fallback; the scheduled job does the regular work
fi
if [[ -r "\$_agent_env" ]]; then
  set -a; source "\$_agent_env"; set +a
fi
unset _agent_env
EOF
  echo "added loader to $zl"; fi

[ -r "$token" ] && "$bin" || echo "next: create the service account into $token, fill $tpl, then run $bin"
