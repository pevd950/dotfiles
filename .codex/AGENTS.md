Keep this file limited to stable, cross-repository personal preferences. More local `AGENTS.md` instructions take precedence.

Todoist is my task manager of choice, do not default new tasks to Inbox. Inspect existing projects, sections, and labels when practical and choose the best fit. Use Inbox only when no suitable location exists or the user explicitly requests it.

Craft is my note taking app of choice and knowledge base, treat it as a rich document system rather than a Markdown sink. Use hierarchy, structured blocks, nested pages, callouts, tables, and light visual formatting when they materially improve readability.

Keep Git operations non-interactive. Never run plain `git rebase --continue` in an agent session because it may open an editor and hang. Use an explicit no-editor form such as `GIT_EDITOR=true git rebase --continue`, and apply the same principle to other commands that might launch an editor.

When using SSH, choose the account based on the task rather than defaulting to `<host>-codex`. Use `<host>-codex` for unattended, noninteractive checks or background work that fits the restricted Codex account and should not require a 1Password approval; use the unsuffixed `<host>` alias when work must run as the user's account or needs user-owned files, apps, Keychain items, permissions, or administrative context. Resolve the intended route with `ssh -G` and, when practical, verify it with a low-risk noninteractive probe; never silently switch identities if it fails unless the user has already authorized that fallback.
