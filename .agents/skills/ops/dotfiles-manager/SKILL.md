---
name: dotfiles-manager
description: Inspect or change yadm-managed dotfiles, global instructions, and personal skills. Use for dotfiles PRs and sync; preserve unrelated live home state.
---

# Dotfiles Manager

The home directory is live operational state, not a scratch repository.

## Working rules

- Scope every yadm command to named paths (`yadm status --short [--untracked-files=all] -- <path>`, `yadm diff [--cached] -- <path>`, `yadm add <path> ...`): a broad status, add or untracked scan from `$HOME` can hang, surface private files, leave yadm locked, or sweep unrelated changes into a commit.
- Apply requested scoped edits directly. The live checkout can hold unrelated local state; leave it out of your commits.
- Before committing shell, app, SSH, GPG, token, credential, or auth-related config, inspect the exact diff for secrets.
- On `index.lock`, verify there is no live yadm/git process before removing or retrying — a lock file is not automatically stale:
  - `ps -axo pid,ppid,stat,command | rg 'yadm|\.local/share/yadm|git'`
  - `ls -l "$(yadm introspect repo)/index.lock"`

## Choose the workspace

Use the live `$HOME` checkout for small targeted edits: a personal skill, one AGENTS/guidance file, a known config file, an already-reviewed sync. Use the developer clone (`DOTFILES_DEV_DIR="${DOTFILES_DEV_DIR:-$HOME/Developer/dotfiles}"`) for bootstrap or install changes, CI/check scripts, restructuring, or changes that should go through PR review. After a dev-clone merge, sync live with `yadm pull --ff-only`, then run only requested follow-ups such as `yadm alt` or `yadm bootstrap`.

## Edit-and-commit loop

Edit exact paths → verify with path-scoped status/diff → validate with the narrowest relevant check → `yadm add <paths>` → review `yadm diff --cached` → commit and push → confirm with `yadm log -1 --oneline` and path-scoped status.

Validation by kind:

- Instruction and skill edits: `scripts/check_instructions.py` (frontmatter and relative links). It reads the yadm index, so a link to a new file passes only after that file is added.
- Shell or bootstrap: the repo check script, if available and safe.
- Config: the tool's non-mutating validation.

## Skill changes

Create only essential files: `SKILL.md`, `agents/openai.yaml` when useful for UI metadata, and `scripts/`, `references/` or `assets/` when needed. Add READMEs or changelogs around skills only when asked.

## Cross-machine portability

Write for multiple Macs and future hosts: use relative or environment-based paths, discover-then-act instead of host constants, and mark intentionally user-specific paths as such. Clone paths, Xcode state, shells and app auth differ per host.

## Developer authentication

For auth, SSH-agent, or token routing work, read [the developer baseline](references/developer-auth.md) and start with its non-mutating preflight. Keep credential repair separately authorized.

## Authority boundaries

Beyond the global confirmation list, live bootstrap execution, package installation and system-defaults changes need authorization for that action and target. Preparing a scoped patch for review does not execute it on the machine.

## Pitfalls

- `codex/...` branch names can collide with existing flat refs in the dotfiles repo; use flat branch names for dotfiles PR branches.
- A generated local machine file does not belong in dotfiles just because it is under `$HOME`.

## Reporting

When committing: exact paths staged, commit SHA, push result, validation run. When not committing: what changed locally and which exact paths need review; if blocked, the blocker and the safest next action.
