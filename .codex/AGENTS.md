Keep global Codex instructions repo-agnostic and free of project-specific workflow.

Use this file only for cross-repo personal preferences that should apply everywhere.

For Todoist, do not default new tasks to Inbox. Inspect existing projects/sections/labels when practical and choose the best fit; use Inbox only when no suitable project exists or the user explicitly asks for it.

For Craft, treat it as a rich document system rather than a plain Markdown sink. Use structured blocks, hierarchy, nested pages, callouts, tables, and light visual formatting when they make notes easier to scan.

Git operations must stay non-interactive. Never run plain `git rebase --continue` in automation or agent sessions because it may open an editor and hang; use an explicit no-editor form such as `GIT_EDITOR=true git rebase --continue`. Apply the same rule to other Git commands that would otherwise launch an editor.

When a repository provides `AGENTS.md` or nested `AGENTS.md` files, treat those as the source of truth for repo-specific workflow, tooling, validation, GitHub process, and coding conventions.

If guidance conflicts, prefer the more local repository instruction over this global file.

Avoid duplicating repository instructions here. Keep this file short, stable, and safe to track in dotfiles.
