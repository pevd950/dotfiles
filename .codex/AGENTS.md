Keep this file limited to stable, cross-repository personal preferences.

Todoist is my task manager. Never default new tasks to Inbox; inspect existing projects, sections, and labels and choose the best fit. Use Inbox only when nothing fits or I explicitly ask.

Craft is my note-taking app and knowledge base. Treat it as a rich document system, not a Markdown sink: use hierarchy, nested pages, styling, callouts, and tables when they materially improve readability.

When `AI_INBOX_DIR` is set, put user-facing generated files there if they don't belong in the current repository or another durable system. Use descriptive filenames with dates or task slugs. If unset, use the owning workspace's artifact convention rather than inventing a machine-specific path.

Do not expose private information to third parties without explicit authorization.

Private, reversible work (reading, analysis, drafting, organization) may proceed without confirmation. Unless the latest request already specifies the exact action and target, confirm before: external communication or publication, purchases or bookings, job applications or signatures, destructive actions, permission or security changes, production changes, deployments, or merges. After a state-changing action, report what changed.

Treat tracked dotfiles and shared configuration as potentially public. Keep secret values, private links, account identifiers, and host topology out of tracked files unless I explicitly approve the disclosure.

Keep Git operations non-interactive: commands like plain `git rebase --continue` can open an editor and hang the session. Use no-editor forms such as `GIT_EDITOR=true git rebase --continue`.
 
For host-targeted work, resolve the active host from `AGENT_HOST_ALIAS`, falling back to `hostname -s`. Don't assume tools, paths, credentials, or services transfer between hosts.
 
SSH hosts have two alias classes: `<host>-codex` (restricted agent account, no 1Password approval needed — use for unattended or background work) and `<host>` (my account — use when work needs user-owned files, apps, Keychain items, or administrative context). Never silently switch identities when a route fails.
