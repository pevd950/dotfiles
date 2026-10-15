#!/usr/bin/env bash
# Agent-only WSL setup. No package installs, shell setup, or bootstrap execution.
set -euo pipefail
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target_home="${HOME:?HOME must be set}"
codex_home="${CODEX_HOME:-$target_home/.codex}"
apply=0
backup_conflicts=0
explicit_target=0
while (($#)); do
  case "$1" in
    --apply) apply=1; shift ;;
    --backup-conflicts) backup_conflicts=1; shift ;;
    --target-home)
      [[ $# -ge 2 && -n "$2" ]] || { echo '--target-home needs a path' >&2; exit 2; }
      target_home="$2"; codex_home="$2/.codex"; explicit_target=1; shift 2 ;;
    --help) echo 'Usage: bash scripts/setup-wsl-agents.sh [--target-home DIR] [--apply] [--backup-conflicts]'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
if (( ! explicit_target )) && ! grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  echo 'This entry point is for WSL; use --target-home for an isolated Linux test.' >&2; exit 1
fi
[[ "$target_home" = /* && "$codex_home" = /* ]] || { echo 'Target paths must be absolute' >&2; exit 1; }
# Global AGENTS.md uses ../.agents links. Do not deploy broken relative references.
[[ "$(dirname -- "$codex_home")" == "$target_home" ]] || { echo 'CODEX_HOME must be directly inside the target home for relative skill references.' >&2; exit 1; }
reject_links() {
  local cursor="$1"
  while [[ "$cursor" != / && -n "$cursor" ]]; do
    [[ ! -L "$cursor" ]] || { echo "Linked destination not managed: $cursor" >&2; exit 1; }
    cursor=$(dirname -- "$cursor")
  done
}
reject_links "$target_home"
reject_links "$codex_home"
[[ ! -s "$codex_home/AGENTS.override.md" ]] || { echo 'AGENTS.override.md shadows guidance; review it first.' >&2; exit 1; }
sources=("$source_root/.codex/AGENTS.md")
targets=("$codex_home/AGENTS.md")
relative=(.codex/AGENTS.md)
while IFS= read -r skill || [[ -n "$skill" ]]; do
  skill=${skill%$'\r'}
  [[ -n "$skill" && "$skill" != \#* ]] || continue
  [[ "$skill" =~ ^[a-z0-9-]+/[a-z0-9-]+$ ]] || { echo "Invalid skill: $skill" >&2; exit 1; }
  skill_source="$source_root/.agents/skills/$skill"
  [[ -f "$skill_source/SKILL.md" ]] || { echo "Missing skill: $skill" >&2; exit 1; }
  if find "$skill_source" -type l -print -quit | grep -q .; then
    echo "Linked source not managed: $skill_source" >&2; exit 1
  fi
  sources+=("$skill_source")
  targets+=("$target_home/.agents/skills/$skill")
  relative+=(".agents/skills/$skill")
done < "$source_root/scripts/agent-skills.txt"
changes=()
conflicts=()
for i in "${!sources[@]}"; do
  target=${targets[$i]}
  if [[ -d "${sources[$i]}" && -L "$target" && $(readlink -- "$target") == "${sources[$i]}" ]]; then
    reject_links "$(dirname -- "$target")"
    continue
  fi
  reject_links "$target"
  if [[ -f "${sources[$i]}" && -f "$target" ]] && cmp -s -- "${sources[$i]}" "$target"; then continue; fi
  changes+=("$i")
  if [[ -e "$target" ]]; then conflicts+=("$i"); fi
  printf 'DEPLOY: %s\n' "$target"
done
echo 'Packages to install: none. Only global instructions and selected skill links.'
if (( ! apply )); then echo 'Preview only. Add --apply after review.'; exit 0; fi
if ((${#conflicts[@]} > 0 && ! backup_conflicts)); then
  echo 'Conflicts found. No changes made. Review and use --backup-conflicts if intended.' >&2; exit 1
fi
if ((${#changes[@]} == 0)); then echo 'Already current; no files changed.'; exit 0; fi
state_root="$target_home/.local/state/dotfiles-agents"
reject_links "$state_root"
reject_links "$state_root/source.txt"
reject_links "$state_root/backups"
mkdir -p "$state_root/backups"
backup_root=$(mktemp -d "$state_root/backups/deploy-XXXXXXXX")
for i in "${changes[@]}"; do
  target=${targets[$i]}
  if [[ -e "$target" ]]; then
    backup="$backup_root/${relative[$i]}"
    mkdir -p "$(dirname -- "$backup")"
    mv -- "$target" "$backup"
  fi
  mkdir -p "$(dirname -- "$target")"
  if [[ -d "${sources[$i]}" ]]; then ln -s -- "${sources[$i]}" "$target"
  else cp -- "${sources[$i]}" "$target"; fi
done
printf '%s\n' "$source_root" > "$state_root/source.txt"
printf 'Deployed. Keep the source work tree at %s; skill links follow its updates.\n' "$source_root"
printf 'Backups (if any): %s\n' "$backup_root"
