#!/usr/bin/env bash
# Run a command with this project's .env.op resolved through 1Password.
# Copy to the repo (for example scripts/op-run.sh), replace PROJECT, and use it to wrap the whole
# process that needs secrets: `scripts/op-run.sh npm test`, `scripts/op-run.sh claude`.
# Wrap the agent or server process, not each command: the Families quota is 1,000 requests/day.
#
# The token comes from ~/.config/op/sa/PROJECT-local.token (the sa-PROJECT-local service account,
# written at setup with mode 0600). An OP_SERVICE_ACCOUNT_TOKEN already in the environment is used
# as is, so CI and direnv keep their own loader, but a local token file that exists with a mode
# other than 0600 is refused either way: a loader that read it would have read a readable secret.
# The token value is never printed.
set -euo pipefail

# Octal mode of a file. GNU stat takes -c and answers --version; BSD/macOS stat takes -f and does not.
# The two invocations are selected explicitly: on GNU, `stat -f` means filesystem status and succeeds
# with the wrong output, so a BSD-then-GNU fallback would never reach the GNU form.
file_mode() {
  if stat --version >/dev/null 2>&1; then
    stat -c '%a' "$1"
  else
    stat -f '%Lp' "$1"
  fi
}

project="PROJECT"
token_file="${OP_SA_TOKEN_FILE:-$HOME/.config/op/sa/${project}-local.token}"
env_file="${OP_ENV_FILE:-.env.op}"

if [ "$#" -eq 0 ]; then
  echo "usage: ${0##*/} <command> [args...]   (runs: op run --env-file $env_file -- <command>)" >&2
  exit 2
fi

command -v op >/dev/null 2>&1 || { echo "op CLI not found; see https://developer.1password.com/docs/cli/get-started/" >&2; exit 1; }
[ -r "$env_file" ] || { echo "$env_file not found; create it from templates/env.op.example or build-env-op.py" >&2; exit 1; }

if [ -e "$token_file" ]; then
  mode="$(file_mode "$token_file")"
  if [ "$mode" != "600" ]; then
    echo "refusing to run: $token_file has mode $mode, expected 600 (chmod 600 \"$token_file\")" >&2
    exit 1
  fi
fi

if [ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]; then
  [ -r "$token_file" ] || { echo "token file $token_file missing; create the sa-${project}-local service account first" >&2; exit 1; }
  OP_SERVICE_ACCOUNT_TOKEN="$(cat "$token_file")"
  export OP_SERVICE_ACCOUNT_TOKEN
fi

exec op run --env-file "$env_file" -- "$@"
