---
name: dotfiles-manager
description: Inspect or change yadm-managed dotfiles, global instructions, and personal skills. Use for dotfiles PRs and sync; preserve unrelated live home state.
---

# Dotfiles Manager

The home directory is live operational state, not a scratch repository. Work with exact paths, stage only named files, and never sweep unrelated home changes into a commit.

## Safety rules

- Do not run broad `yadm status --untracked-files=all` from `$HOME` unless the user explicitly asks. Prefer path-scoped commands: `yadm status --short [--untracked-files=all] -- <path>`, `yadm diff [--cached] -- <path>`.
- Stage only explicit paths with `yadm add <path> ...`. Never `yadm add -A`, broad `git add`, or broad untracked scans in `$HOME`.
- Apply requested scoped edits without renewed approval. Isolate PR work from live home files; preserve unrelated changes.
- Before committing shell, app, SSH, GPG, token, credential, or auth-related config, inspect the exact diff for secrets.
- On `index.lock`, verify there is no live yadm/git process before removing or retrying — a lock file is not automatically stale:
  - `ps -axo pid,ppid,stat,command | rg 'yadm|\.local/share/yadm|git'`
  - `ls -l "$(yadm introspect repo)/index.lock"`

## Choose the workspace

Use the live `$HOME` checkout for small targeted edits: a personal skill, one AGENTS/guidance file, a known config file, an already-reviewed sync. Use the developer clone (`DOTFILES_DEV_DIR="${DOTFILES_DEV_DIR:-$HOME/Developer/dotfiles}"`) for bootstrap or install changes, CI/check scripts, restructuring, or changes that should go through PR review. After a dev-clone merge, sync live with `yadm pull --ff-only`, then run only requested follow-ups such as `yadm alt` or `yadm bootstrap`.

## Edit-and-commit loop

Edit exact paths → verify with path-scoped status/diff → validate with the narrowest relevant check (skills: read `SKILL.md` and `agents/openai.yaml`; shell/bootstrap: the repo check script if available and safe; config: the tool's non-mutating validation) → `yadm add <paths>` → review `yadm diff --cached` → commit and push → confirm with `yadm log -1 --oneline` and path-scoped status.

## Skill changes

Canonical root: `SKILL_ROOT="$HOME/.agents/skills"`, organized by category (for example `development/<skill-name>/SKILL.md`). Create only essential files: `SKILL.md`, `agents/openai.yaml` when useful for UI metadata, and `scripts/`/`references/`/`assets/` only when genuinely needed. No READMEs or changelogs around skills unless asked.

## Cross-machine portability

Write for multiple Macs and future hosts: no hardcoded project paths when a relative or environment-based description works; do not assume identical clone paths, Xcode state, shells, or app auth; prefer discover-then-act over host-specific constants; mark intentionally user-specific paths as such.

## Developer authentication

For auth, SSH-agent, or token routing work, read [the developer baseline](references/developer-auth.md) and start with its non-mutating preflight. Keep credential repair separately authorized.

## Authority boundaries

Confirm destructive home changes, live bootstrap execution, credential/security changes, package installation, system defaults, and human review replies unless already explicitly authorized for that action and target. Preparing a scoped patch for review does not execute it on the machine. Never commit unrelated changes without authorization.

## Pitfalls

- Broad home scans can hang, surface private noise, or leave yadm locked.
- The live checkout can hold unrelated local state; a clean-looking summary is not permission to commit it.
- `codex/...` branch names can collide with existing flat refs in the dotfiles repo; prefer flat branch names for dotfiles PR branches.
- A generated local machine file does not belong in dotfiles just because it is under `$HOME`.

## Reporting

When committing: exact paths staged, commit SHA, push result, validation run. When not committing: what changed locally and which exact paths need review; if blocked, the blocker and the safest next action.
