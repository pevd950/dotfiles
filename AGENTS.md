# Dotfiles Agent Guidance

## Scope
- This repo manages dotfiles only. `$HOME` is not a single git repo.
- Use `yadm` only on tracked files; run `yadm ls-files` before broad edits.
- Do not modify or stage files inside other git repos under `$HOME` unless explicitly requested.

## Workflow
- Prefer additive, idempotent changes in bootstrap/setup.
- Keep secrets out of yadm (e.g., `~/.config/gh/hosts.yml`, `~/.ssh/*`, `~/.gnupg/*`, tokens).
- Treat `~/.config/agent-skills/skills/` as the canonical personal/shared skills source; create or update skills there by default and symlink/mirror provider-specific skill directories instead of creating divergent copies.
- If a dotfile change should apply across Pablo's hosts, make it through yadm-tracked files and check whether the local host is current with the yadm remote before editing when practical.
- If a change is host-local, keep it out of yadm-tracked portable files and state that scope explicitly.
