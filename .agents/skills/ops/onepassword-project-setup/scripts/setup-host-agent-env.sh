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
bin="$HOME/.local/bin/refresh-agent-env"
# A rerun keeps the token file the installed renderer already uses, so a host set up with --token-file
# is not silently repointed at the default path.
if [ -z "$token" ] && [ -r "$bin" ]; then
  previous="$(sed -n 's/^.*tok=\([^;]*\).*$/\1/p' "$bin" | head -1)"; previous="${previous%\"}"; previous="${previous#\"}"
  if [ -r "$previous" ]; then token="$previous"; fi
fi
token="${token:-$HOME/.config/op/sa/$alias-agents.token}"
envdir="$HOME/.config/op/env"; tpl="$envdir/$alias-agent.env.tpl"; out="$envdir/$alias-agent.env"
umask 077; mkdir -p "$envdir" "$HOME/.local/bin"; chmod 700 "$envdir"

{
  printf '#!/bin/zsh -f\n'
  printf 'tpl=%q; out=%q; tok=%q\n' "$tpl" "$out" "$token"
  cat <<'EOF'
# Render $out from the 1Password references in $tpl with the token in $tok. Safe to rerun.
# -f skips startup files: the ~/.zshenv.local loader calls this script, so reading it here would recurse.
# Shells source the rendered file, so every value is written single-quoted: a stored value is always
# data and can never run as shell code. A value must be a single line.
set -euo pipefail
[[ -n "${REFRESH_AGENT_ENV_ACTIVE:-}" ]] && exit 0; export REFRESH_AGENT_ENV_ACTIVE=1
fail() { echo "refresh-agent-env: $1, keeping previous file" >&2; exit 1; }
[[ -r "$tok" ]] || fail "missing $tok"
[[ -r "$tpl" ]] || fail "missing $tpl"
export OP_SERVICE_ACCOUNT_TOKEN="$(<"$tok")"
umask 077; work="$(mktemp -d "$out.XXXXXX")"; trap 'rm -rf "$work"' EXIT

# 1. Reduce the template to one NAME=reference line per variable. Comment lines, "export", quotes
#    around the reference and a trailing comment are template conveniences, not part of the value.
names=(); : > "$work/tpl"
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ '^[[:space:]]*(#.*)?$' ]] && continue
  [[ "$line" =~ '^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$' ]] || fail "a template line is not NAME=reference"
  name="$match[2]"; value="$match[3]"
  if [[ "$value" =~ '^"([^"]*)"[[:space:]]*(#.*)?$' || "$value" =~ "^'([^']*)'[[:space:]]*(#.*)?\$" ]]; then value="$match[1]"
  elif [[ "$value" =~ '^(.*[^[:space:]])?[[:space:]]+#.*$' ]]; then value="$match[1]"
  elif [[ "$value" =~ '^(.*[^[:space:]])?[[:space:]]*$' ]]; then value="$match[1]"; fi
  (( ${names[(Ie)$name]} )) && fail "$name appears twice in the template"
  names+=("$name"); print -r -- "$name=$value" >> "$work/tpl"
done < "$tpl"
(( ${#names} )) || fail "the template has no variables yet"

# 2. Resolve the references in one call.
op inject -i "$work/tpl" -o "$work/rendered" --force >/dev/null || fail "1Password could not resolve the template"

# 3. Pair each result line with its variable and write it quoted.
rendered=("${(@f)$(<"$work/rendered")}")
(( ${#rendered} == ${#names} )) || fail "a value spans several lines (${#names} variables, ${#rendered} result lines)"
print -r -- "# Rendered by refresh-agent-env from $tpl. Edit the template, not this file." > "$work/out"
for (( i = 1; i <= ${#names}; i++ )); do
  name="$names[$i]"; line="$rendered[$i]"
  [[ "$line" == "$name="* ]] || fail "result line $i does not belong to $name"
  value="${line#"$name="}"
  [[ "$value" == *op://* ]] && fail "unresolved reference for $name"
  print -r -- "$name=${(qq)value}" >> "$work/out"
done
mv -f "$work/out" "$out"; chmod 600 "$out"; echo "rendered $out (${#names} vars)"
EOF
} > "$bin"
chmod 700 "$bin"

if [ ! -e "$tpl" ]; then cat > "$tpl" <<EOF
# $alias shared agent and shell secrets, as 1Password references (no values).
# One NAME=<reference> line per variable (reference = vault, item ID and field after the op scheme),
# with the item title in a comment. Values are data: a line holds a reference or a literal, never shell syntax.
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
