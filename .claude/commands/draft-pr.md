---
allowed-tools: Bash, Edit, MultiEdit, Write, Read, Glob, Grep
argument-hint: [title]
description: Intelligently create a draft PR based on current changes
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --porcelain`
- Uncommitted changes: !`git diff HEAD`
- Commits not in base: !`git log --oneline origin/main..HEAD`
- Full diff from base: !`git diff origin/main...HEAD`
- Remote tracking: !`git status -sb`
- Recent commits in base: !`git log --oneline -5 origin/main`
- All local branches: !`git branch -a`
- Current commit: !`git rev-parse --short HEAD`

## Your Task

Based on the context above, intelligently create a DRAFT pull request. Follow these steps:

1. **Analyze the current state:**
   - Check if we're on the main/master branch or a feature branch
   - Determine if there are uncommitted changes that need to be committed first
   - Check if the current branch has commits not in the base branch
   - Verify if the branch is tracking a remote branch

2. **Smart branch handling:**
   - If on main/master with uncommitted changes: create a new feature branch with a descriptive name based on the changes
   - If on a feature branch: use the current branch
   - If no commits ahead of base but have uncommitted changes: commit them first

3. **Create the DRAFT PR:**
   - Always create as a draft PR using the --draft flag
   - If argument provided: use $1 as PR title
   - Otherwise: generate a concise, descriptive title from the changes
   - Write a comprehensive PR description including:
     - Summary of changes (2-4 bullet points)
     - Type of change (feature, bugfix, refactor, etc.)
     - Testing recommendations
     - Any breaking changes or migration notes
   
4. **Handle edge cases:**
   - If branch needs to be pushed to remote, do so with -u flag
   - If no changes to create PR from, inform the user
   - If multiple unrelated changes detected, suggest splitting into multiple PRs

5. **Final output:**
   - Return the PR URL
   - Suggest next steps if applicable (e.g., "Consider adding tests for...")

Be smart about branch naming - use kebab-case and include the type of change (e.g., feature/user-auth, fix/memory-leak, refactor/api-client).

Always use the --draft flag when creating the PR with gh pr create.
Do not add "[DRAFT]" to the title since GitHub will handle the draft status visually.