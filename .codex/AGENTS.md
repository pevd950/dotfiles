Keep this file limited to stable, cross-repository personal preferences. More local `AGENTS.md` instructions take precedence.

For Todoist, do not default new tasks to Inbox. Inspect existing projects, sections, and labels when practical and choose the best fit. Use Inbox only when no suitable location exists or the user explicitly requests it.

For Craft, treat it as a rich document system rather than a Markdown sink. Use hierarchy, structured blocks, nested pages, callouts, tables, and light visual formatting when they materially improve readability.

Keep Git operations non-interactive. Never run plain `git rebase --continue` in an agent session because it may open an editor and hang. Use an explicit no-editor form such as `GIT_EDITOR=true git rebase --continue`, and apply the same principle to other commands that might launch an editor.
