---
name: dotfiles-manager
description: Safely inspect, edit, commit, push, or sync the user's yadm-managed dotfiles. Use when working on files under the home-directory dotfiles checkout, `~/.config/agent-skills`, global AGENTS guidance, shell/app config, bootstrap scripts, or when the user asks for yadm, dotfiles, cross-machine config, or live-home repo changes. Prioritize exact-path yadm operations and avoid broad `$HOME` scans.
---

# Dotfiles Manager

## Core Rule

The home directory is live operational state, not a scratch repository. Work with exact paths, stage only named files, and never sweep unrelated home changes into a commit.

## Safety Rules

- Do not run broad `yadm status --untracked-files=all` from `$HOME` unless the user explicitly asks.
- Prefer path-scoped commands:
  - `yadm status --short -- <path>`
  - `yadm status --short --untracked-files=all -- <path>`
  - `yadm diff -- <path>`
  - `yadm diff --cached -- <path>`
- Stage only explicit paths with `yadm add <path> ...`.
- Never use `yadm add -A`, broad `git add`, or broad untracked scans in `$HOME`.
- Before deleting or changing home files, ask unless the user explicitly requested that exact mutation.
- Before committing shell, app, SSH, GPG, token, credential, or auth-related config, inspect the exact diff for secrets.
- If yadm reports `index.lock`, check for live `yadm` or `git` processes before removing or retrying:
  - `ps -axo pid,ppid,stat,command | rg 'yadm|\\.local/share/yadm|git'`
  - `YADM_REPO="$(yadm introspect repo)" && ls -l "$YADM_REPO/index.lock"`

## Choose The Right Workspace

Use the live `$HOME` yadm checkout only for small, targeted edits such as:

- adding or updating a personal skill
- updating a single AGENTS/global guidance file
- committing a known exact config file
- syncing an already-reviewed dotfiles change

Use the developer clone for larger work. Resolve it with:

```bash
DOTFILES_DEV_DIR="${DOTFILES_DEV_DIR:-$HOME/Developer/dotfiles}"
```

Prefer that clone for:

- bootstrap or install workflow changes
- CI/check scripts
- restructuring tracked dotfiles
- changes that should go through PR review before affecting the live home

After a developer-clone PR merges, sync the live checkout with non-interactive commands such as `yadm pull --ff-only`, then run only the requested follow-up commands like `yadm alt` or `yadm bootstrap`.

## Small Live-Home Edit Workflow

1. Identify the exact paths the user asked to change.
2. Read only those files and any directly related local instructions.
3. Edit with `apply_patch`.
4. Verify exact-path state:
   - `yadm status --short --untracked-files=all -- <path1> <path2>`
5. Review the exact diff:
   - `yadm diff -- <path1> <path2>`
6. Validate with the narrowest relevant check:
   - for skills: read `SKILL.md` and `agents/openai.yaml`
   - for shell/bootstrap: run the repo check script if available and safe
   - for config: run the tool's non-mutating validation if available
7. Stage exact paths:
   - `yadm add <path1> <path2>`
8. Check staged diff:
   - `yadm diff --cached --stat`
   - `yadm diff --cached -- <path1> <path2>`
9. Commit and push:
   - `yadm commit -m "<message>"`
   - `yadm push`
10. Confirm:
   - `yadm log -1 --oneline`
   - `yadm status --short --untracked-files=all -- <path1> <path2>`

## Skill Changes

For personal skills, treat this as the canonical root unless the user names another root:

```bash
SKILL_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}/agent-skills/skills"
```

Create only essential skill files:

- `SKILL.md`
- `agents/openai.yaml` when useful for UI metadata
- optional `scripts/`, `references/`, or `assets/` only when the skill genuinely needs them

Keep `SKILL.md` concise and operational. Do not add READMEs, changelogs, or extra docs around the skill unless the user asks.

## Cross-Machine Portability

Write dotfiles guidance for multiple Macs and future hosts:

- Avoid hardcoded project paths when a relative or environment-based description works.
- Do not assume every host has the same repo clone paths, Xcode state, shells, or app auth.
- Prefer "discover then act" instructions over host-specific constants.
- If a path is intentionally user-specific, make that explicit.

## When To Ask First

Ask before proceeding when the task involves:

- deleting, moving, or rewriting broad home-directory files
- changing bootstrap behavior that could mutate a machine
- secrets, credentials, SSH/GPG config, LaunchAgents, browser/app auth, or password-manager state
- installing packages or changing system defaults
- responding to human review comments in dotfiles PRs
- committing unrelated yadm changes you did not create

## Common Pitfalls

- Broad home scans can hang, find private noise, or leave yadm locked.
- The live yadm checkout can have unrelated local state; do not infer it is safe to commit from a broad clean-looking summary.
- `codex/...` branch names can collide with existing flat refs in the dotfiles repo. Prefer flat branch names when creating dotfiles PR branches.
- A yadm lock file is not automatically stale. Verify there is no live process before retrying or removing it.
- Do not assume a generated local machine file belongs in dotfiles just because it is under `$HOME`.

## Output Expectations

When committing:

- Say exactly which paths were staged.
- Include the commit SHA.
- Say whether push succeeded.
- Mention any validation run.

When not committing:

- State what changed locally and which exact paths need review.
- If blocked, name the blocker and the safest next action.
