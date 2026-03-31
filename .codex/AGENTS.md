Keep global Codex instructions repo-agnostic and free of project-specific workflow.

Use this file only for cross-repo personal preferences that should apply everywhere.

Git operations must stay non-interactive. Never run plain `git rebase --continue` in automation or agent sessions because it may open an editor and hang; use an explicit no-editor form such as `GIT_EDITOR=true git rebase --continue`. Apply the same rule to other Git commands that would otherwise launch an editor.

When a repository provides `AGENTS.md` or nested `AGENTS.md` files, treat those as the source of truth for repo-specific workflow, tooling, validation, GitHub process, and coding conventions.

If guidance conflicts, prefer the more local repository instruction over this global file.

Avoid duplicating repository instructions here. Keep this file short, stable, and safe to track in dotfiles.
