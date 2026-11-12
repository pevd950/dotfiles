#!/usr/bin/env bash
# Keep agent skills in step with their sources. Safe to run at any time and quiet
# unless something changes. Run by yadm bootstrap and after every `yadm pull`.
#
# 1. Xcode skills: when the selected Xcode's build differs from the last synced
#    one, replace ~/.agents/skills/xcode with the skills Xcode ships.
# 2. Claude Code: link every personal skill into ~/.claude/skills, and drop links
#    that are broken. Claude reads no nested skills root, so it needs one link per
#    skill. On a host that has Xcode's plugin installed for Claude, the plugin
#    supplies the Xcode skills and they are not linked a second time.
set -euo pipefail

skills_root="$HOME/.agents/skills"
xcode_skills="$skills_root/xcode"
claude_dir="$HOME/.claude/skills"
# Present only on hosts where Xcode's plugin was installed for Claude.
claude_xcode_plugin="$HOME/.local/share/xcode-agent-plugin/xcode-integration"

# Copy a directory Xcode exported (read-only files) over a generated destination.
replace_dir() {
  local src="$1" dest="$2" tmp
  tmp="$(mktemp -d "$(dirname "$dest")/.sync.XXXXXX")"
  cp -R "$src/." "$tmp/"
  chmod -R u+w "$tmp"
  if [[ -e "$dest" ]]; then
    chmod -R u+w "$dest"
    rm -rf "$dest"
  fi
  mv "$tmp" "$dest"
}

sync_xcode_skills() {
  command -v xcrun >/dev/null 2>&1 || return 0
  local build stamp exported
  build="$(xcodebuild -version 2>/dev/null | awk '/Build version/ {print $3}')" || return 0
  [[ -n "$build" ]] || return 0
  stamp="$xcode_skills/.xcode-build"
  if [[ -f "$stamp" && "$(cat "$stamp")" == "$build" ]]; then
    return 0
  fi
  # The packaged plugin carries every Xcode skill; `skills export` leaves some out.
  exported="$(xcrun agent plugin path --plugin-format codex 2>/dev/null | tail -1)" || return 0
  [[ -d "$exported/skills" ]] || return 0
  replace_dir "$exported/skills" "$xcode_skills"
  printf '%s\n' "$build" > "$stamp"
  echo "Xcode skills refreshed for build $build"

  if [[ -d "$claude_xcode_plugin" ]]; then
    exported="$(xcrun agent plugin path --plugin-format claude 2>/dev/null | tail -1)" || return 0
    [[ -d "$exported/skills" ]] || return 0
    replace_dir "$exported" "$claude_xcode_plugin"
    echo "Xcode plugin for Claude refreshed for build $build"
  fi
}

link_claude_skills() {
  [[ -d "$skills_root" ]] || return 0
  mkdir -p "$claude_dir"
  local link dest skill name
  shopt -s nullglob
  for link in "$claude_dir"/*; do
    [[ -L "$link" ]] || continue
    dest="$(readlink "$link" || true)"
    if [[ ! -e "$link" ]]; then
      echo "Removing broken Claude skill link: $(basename "$link")"
      rm "$link"
    elif [[ -d "$claude_xcode_plugin" && "$dest" == "$xcode_skills"/* ]]; then
      echo "Removing Claude skill link the Xcode plugin replaces: $(basename "$link")"
      rm "$link"
    fi
  done
  for skill in "$skills_root"/* "$skills_root"/*/*; do
    [[ -f "$skill/SKILL.md" ]] || continue
    if [[ -d "$claude_xcode_plugin" && "$skill" == "$xcode_skills"/* ]]; then
      continue
    fi
    name="$(basename "$skill")"
    link="$claude_dir/$name"
    [[ -e "$link" || -L "$link" ]] && continue
    ln -s "$skill" "$link"
    echo "Linked Claude skill: $name"
  done
  shopt -u nullglob
}

sync_xcode_skills
link_claude_skills
