---
name: github-release-dispatch
description: Agent-driven production deploys through a GitHub App identity. Use when Pablo asks an agent to deploy, release, ship or roll out a project to production (or staging) via its GitHub Actions deploy workflow. Mints a short-lived installation token from the project's 1Password item, requires Pablo's explicit go for that specific deploy, dispatches the workflow, watches the run, and notifies him. Never for local builds, TestFlight-only flows, or repositories without a config file here.
---

# GitHub release dispatch

One identity per project (a GitHub App installed only on that repository, credentials in that project's Prod vault), one short-lived token per deploy, one explicit go from Pablo per deploy. GitHub records the app as the dispatching actor; this skill records the approval and the run locally.

## When to use

- "Deploy plato-ai to production", "ship main", "roll out sha-abc1234", "deploy staging now".
- Not for: building locally, Xcode Cloud / TestFlight (separate), repos with no `config/projects/<project>.env` here (add one first, see below).

## The gate (non-negotiable)

1. **Identify the exact deploy**: project, environment, image tag. Resolve the tag yourself (`scripts/resolve-image-tag.sh <project> [ref]`) and show it to Pablo. Never deploy "latest" to production without naming the sha.
2. **Get Pablo's explicit go for that deploy.** A go is a message from Pablo, in this session or as a reply to a notification, that names the environment (and, for production, the tag or "that one"). A standing instruction like "deploy whenever CI is green" is not a go. If Pablo is not in the session, send one request through `$notify-user` (title `Release`, message with project, environment, tag, what changed, and "reply deploy to proceed") and wait for his reply. Do not assume consent from silence, from a Todoist task, or from a green check.
3. **Production additionally requires** the repository variable named in the config (`ALLOW_PRODUCTION_DEPLOY` for plato-ai) to be `true`. `scripts/dispatch-deploy.sh` sets it with Pablo's own `gh` auth on this host only when you pass `--approval` text quoting his go, and resets it to `false` when the run finishes. If `gh` is not authenticated as Pablo here, ask him to set the variable from GitHub instead.

## Steps

```bash
S="$HOME/.agents/skills/ops/github-release-dispatch"
"$S/scripts/resolve-image-tag.sh" plato-ai main            # prints sha-<7> of the latest built main commit, or the ref's sha
"$S/scripts/dispatch-deploy.sh" plato-ai production sha-abc1234 --approval "Pablo 2026-10-27 14:05 'deploy sha-abc1234 to prod'"
```

What `dispatch-deploy.sh` does: reads the project config; mints an installation token from the 1Password item (desktop-app auth or a service account token in `OP_SERVICE_ACCOUNT_TOKEN`); verifies the token sees the repository; for production, checks or sets the gate variable; runs `gh workflow run <workflow> --ref <ref> -f environment=<env> -f image-tag=<tag>` with `GH_TOKEN` set to the installation token; finds the new run; watches it to completion; prints the run URL and conclusion; appends an audit line to `~/.local/state/github-release-dispatch/deploys.log`; resets the gate variable.

4. **Notify**: after the run finishes, send the result through `$notify-user` (project, environment, tag, conclusion, run URL). Also when it fails.
5. **Record**: add a line to the project's Craft page or the deploy log in Todoist if Pablo tracks releases there; never paste tokens anywhere.

## Secrets handling

- The installation token lives only in the script's environment and expires in one hour. Never echo it, never put it in a file, never pass it on a command line (`GH_TOKEN` env only).
- The app private key is read with `op read` inside the script and never written to disk.
- Production secrets are not involved here at all: the workflow reads them from the GitHub `production` environment (1Password `sa-<project>-release`).

## Adding a project

Create `config/projects/<project>.env` with `REPO`, `WORKFLOW_FILE`, `DEFAULT_REF`, `OP_APP_ITEM` (an `op://Vault/Item` base whose item has `app_id`, `installation_id`, `private_key` fields), `GATE_VAR` (empty if the workflow has no variable gate), `ENV_INPUT`, `TAG_INPUT`, `PROD_ENV_NAME`. Create the GitHub App through the manifest flow (actions: write, contents: read, metadata: read; install only on that repo) and store its credentials in the project's Prod vault.

## Failure modes

- `op read` prompts for approval: Pablo must approve in 1Password (desktop auth) unless a release-agent service account token is exported. If he is away, notify and wait; do not retry in a loop.
- 403 on dispatch: the app is not installed on the repo or lacks `actions: write`.
- Gate variable not `true` and no `--approval`: the script stops. That is the point.
- Run not found after dispatch: wait 10 seconds and list runs for the workflow; never dispatch twice.
