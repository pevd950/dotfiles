---
name: dotfiles-manager
description: Safely inspect, edit, commit, push, or sync the user's yadm-managed dotfiles. Use when working on files under the home-directory dotfiles checkout, `~/.agents/skills`, global AGENTS guidance, shell/app config, bootstrap scripts, or when the user asks for yadm, dotfiles, cross-machine config, or live-home repo changes. Prioritize exact-path yadm operations and avoid broad `$HOME` scans.
---

# Dotfiles Manager

The home directory is live operational state, not a scratch repository. Work with exact paths, stage only named files, and never sweep unrelated home changes into a commit.

## Safety rules

- Do not run broad `yadm status --untracked-files=all` from `$HOME` unless the user explicitly asks. Prefer path-scoped commands: `yadm status --short [--untracked-files=all] -- <path>`, `yadm diff [--cached] -- <path>`.
- Stage only explicit paths with `yadm add <path> ...`. Never `yadm add -A`, broad `git add`, or broad untracked scans in `$HOME`.
- Before deleting or changing home files, ask unless the user explicitly requested that exact mutation.
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

## 1Password developer baseline

For 1Password, GitHub auth, SSH agent, or developer-token routing work, start with the non-mutating preflight, and use it to classify the host, not to collect secrets:

```bash
~/.zshrc_custom/bin/onepassword-dev-preflight
```

It answers: whether `op`, 1Password.app, `onepassword-mcp`, and the Codex `1password` MCP entry are available; whether `op account list`, `op plugin list`, `gh auth status`, and `gh api user` run without printing their output; whether `GH_TOKEN`/`GITHUB_TOKEN` env overrides are masking the baseline; whether `SSH_AUTH_SOCK`, `ssh-add`, 1Password `agent.toml`, GitHub `IdentityAgent`, and SSH auth to GitHub are usable; and which variable names quiet local env files export, without values.

Run the mutating `scripts/setup-1password-dev.zsh` only after the baseline shows the intended gap or the user asked for repair. Keep tracked guidance to command names, variable names, and non-secret mechanics; never commit private 1Password item paths, vault IDs, token values, host-local Craft links, or generated secret files. For remote hosts, verify inheritance by pulling the yadm commit there and re-running the preflight — do not assume local 1Password app, SSH socket, or CLI auth state exists remotely.

## Ask first

Deleting, moving, or rewriting broad home-directory files; bootstrap changes that could mutate a machine; secrets, credentials, SSH/GPG config, LaunchAgents, browser/app auth, or password-manager state; installing packages or changing system defaults; responding to human review comments in dotfiles PRs; committing unrelated yadm changes you did not create.

## Pitfalls

- Broad home scans can hang, surface private noise, or leave yadm locked.
- The live checkout can hold unrelated local state; a clean-looking summary is not permission to commit it.
- `codex/...` branch names can collide with existing flat refs in the dotfiles repo; prefer flat branch names for dotfiles PR branches.
- A generated local machine file does not belong in dotfiles just because it is under `$HOME`.

## Reporting

When committing: exact paths staged, commit SHA, push result, validation run. When not committing: what changed locally and which exact paths need review; if blocked, the blocker and the safest next action.
