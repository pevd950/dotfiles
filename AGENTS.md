# Dotfiles Agent Guidance

## Scope
- This repo manages dotfiles only. `$HOME` is not a single git repo.
- Use `yadm` only on tracked files; run `yadm ls-files` before broad edits.
- Do not modify or stage files inside other git repos under `$HOME` unless explicitly requested.

## Workflow
- Prefer additive, idempotent changes in bootstrap/setup.
- Keep secrets out of yadm (e.g., `~/.config/gh/hosts.yml`, `~/.ssh/*`, `~/.gnupg/*`, tokens).
- Treat `~/.config/agent-skills/skills/` as the canonical skills source; symlink elsewhere.
