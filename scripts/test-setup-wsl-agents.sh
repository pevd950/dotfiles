#!/usr/bin/env bash
set -euo pipefail
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test_root=$(mktemp -d)
trap 'rm -rf -- "$test_root"' EXIT
target="$test_root/profile with spaces"
installer="$source_root/scripts/setup-wsl-agents.sh"
bash "$installer" --target-home "$target"
test ! -e "$target"
mkdir -p "$target/.codex"
printf 'local guidance\n' > "$target/.codex/AGENTS.md"
if bash "$installer" --target-home "$target" --apply; then
  echo 'Conflict accepted without backup flag' >&2; exit 1
fi
test ! -e "$target/.agents"
bash "$installer" --target-home "$target" --apply --backup-conflicts
grep -q 'Craft is my knowledge base' "$target/.codex/AGENTS.md"
test -L "$target/.agents/skills/productivity/craft"
test -f "$target/.agents/skills/productivity/craft/references/formatting.md"
test ! -e "$target/.agents/skills/design"
find "$target/.local/state/dotfiles-agents/backups" -name AGENTS.md -exec grep -l 'local guidance' {} \; | grep -q .
bash "$installer" --target-home "$target" --apply | grep -q 'Already current'
printf 'override\n' > "$target/.codex/AGENTS.override.md"
if bash "$installer" --target-home "$target" --apply; then
  echo 'Shadowing override accepted' >&2; exit 1
fi
mkdir -p "$test_root/linked" "$test_root/outside"
ln -s "$test_root/outside" "$test_root/linked/.agents"
if bash "$installer" --target-home "$test_root/linked" --apply; then
  echo 'Linked destination accepted' >&2; exit 1
fi
test -z "$(ls -A "$test_root/outside")"
backup_home="$test_root/backup-profile"
mkdir -p "$backup_home/.codex" "$backup_home/.local/state/dotfiles-agents"
printf 'preserve backup fixture\n' > "$backup_home/.codex/AGENTS.md"
ln -s "$test_root/outside" "$backup_home/.local/state/dotfiles-agents/backups"
if bash "$installer" --target-home "$backup_home" --apply --backup-conflicts; then
  echo 'Linked backup directory accepted' >&2; exit 1
fi
test -z "$(ls -A "$test_root/outside")"
grep -qx 'preserve backup fixture' "$backup_home/.codex/AGENTS.md"
echo 'PASS: WSL agent deployment safety tests'
