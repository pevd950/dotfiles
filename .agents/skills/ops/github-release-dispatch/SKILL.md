---
name: github-release-dispatch
description: Release a project to staging or production through its GitHub Actions release path - a protected v* tag where the project promotes by tag, or a workflow dispatch through a reviewed GitHub App identity where it does not. Use when Pablo asks to deploy, release, ship or roll out a project.
---

# GitHub release dispatch

Every release needs one go from Pablo. Local builds and Xcode Cloud or TestFlight flows are separate.

## Which path

Read the project's `docs/HOW_IT_SHIPS.md` (or its release docs) first.

- **Tag promotion** (indie-infra ADR 0009): merging to `main` deploys staging and records the deployed artifact. Production is a protected `v*` tag on a commit that staging recorded; the release workflow verifies that record and promotes the same artifact, with nothing rebuilt. Staging never needs a dispatch.
- **Manual dispatch**: a project with a release-dispatch manifest that has not adopted tag promotion, or a redeploy of a specific image. One job-specific GitHub App within its approved repository and installation scope, one short-lived token per deploy. Plato keeps this path until [#2871](https://github.com/pevd950/plato-ai/issues/2871) closes.

## The gate

1. **Identify the exact release**: project, environment, and the commit (tag path) or image tag (dispatch path, resolved with `scripts/resolve-image-tag.sh <project> [ref]`). Show it to Pablo. Production always names a sha or version, never "latest".
2. **Have a go from Pablo that covers this deploy.** Two forms count, and nothing else does:
   - an explicit message from Pablo, in this session or as a reply to a notification, naming the environment (and, for production, the tag or "that one");
   - a **standing grant** Pablo wrote with explicit scope and expiry: `STANDING_APPROVAL_STAGING` / `STANDING_APPROVAL_PRODUCTION` plus the matching `_UNTIL` date (YYYY-MM-DD, UTC; the script ignores an undated or expired grant) in the app manifest, or an in-session statement that names project, environment, conditions and how long it lasts ("deploy plato-ai staging whenever main is green this week"). Check the scope and expiry before relying on it; production is never covered by a grant that does not name production.

   A vague or implied instruction is not a go, and neither is silence, a Todoist task or a green check. When no go covers the deploy, ask in chat and send one request through `notify-user` (subtitle `Release`; message with project, environment, tag, what changed, and "reply deploy to proceed"), then wait for his reply.
3. **Dispatched production additionally requires** the repository variable named in the manifest (`ALLOW_PRODUCTION_DEPLOY` for plato-ai) to be `true`. `scripts/dispatch-deploy.sh` sets it with Pablo's own `gh` auth on this host only when you pass `--approval` text quoting his go, and resets it to `false` when the run finishes. If `gh` is not authenticated as Pablo here, ask him to set the variable from GitHub.

## Tag promotion

Check that staging recorded the commit (a GitHub Deployment in the staging environment for that sha); the release workflow refuses a commit without one. Then tag and push with Pablo's go in the message:

```bash
git tag -a v1.4.0 <sha> -m "Release v1.4.0. Pablo's go: 2026-11-13 14:05 'ship v1.4.0'"
git push origin v1.4.0
gh run list --repo <owner>/<repo> --workflow <release workflow> --limit 1   # watch it to the end
```

Only repository administrators can create a `v*` tag, and no one can move or delete one. A bad release gets a new version, never a moved tag.

## Manual dispatch

```bash
S="$HOME/.agents/skills/ops/github-release-dispatch"
"$S/scripts/resolve-image-tag.sh" plato-ai main            # prints sha-<7> of the latest built main commit, or the ref's sha
"$S/scripts/dispatch-deploy.sh" plato-ai production sha-abc1234 --approval "Pablo 2026-10-27 14:05 'deploy sha-abc1234 to prod'"
```

`dispatch-deploy.sh` reads the manifest, mints an installation token from the 1Password item (desktop-app auth or a service account token in `OP_SERVICE_ACCOUNT_TOKEN`), verifies the token sees the repository, checks or sets the production gate variable, runs `gh workflow run <workflow> --ref <ref> -f environment=<env> -f image-tag=<tag>` with `GH_TOKEN` set to the installation token, watches the new run, prints its URL and conclusion, appends an audit line to `~/.local/state/github-release-dispatch/deploys.log`, and resets the gate variable.

For either path, when the run finishes, pass or fail, send the result through `notify-user` (project, environment, tag, conclusion, run URL) and record the tag and run URL on the project's workboard: tick the release's row, or add one.

## Secrets

The installation token lives only in the script's environment (`GH_TOKEN`) and expires in one hour; keep it out of output, files and command lines. The script reads the app private key with `op read` and never writes it to disk. Production secrets are not involved: the workflow reads them from the GitHub `production` environment (1Password `sa-<project>-release`).

## Adding a project

A project's manifest is `control-plane/apps/<project>/release-dispatch.env` in indie-infra, reviewed through a PR, with no secret values. The scripts read it from indie-infra's `main` on the remote, through the clone at `~/Developer/indie-infra` and whatever branch that clone has checked out, and stop when `main` cannot be refreshed. `RELEASE_DISPATCH_CONFIG_DIR` reads a directory as it is, for trying a manifest still in review; production refuses it.

- `REPO`, `WORKFLOW_FILE`, `DEFAULT_REF`, `ENV_INPUT`, `TAG_INPUT`, `PROD_ENV_NAME`: select the caller. `BUILD_WORKFLOW_FILE` is optional; `GATE_VAR` is empty when the workflow has no variable gate.
- `OP_APP_ITEM`: the approved `op://Vault/Item` base with `app_id`, `installation_id` and `private_key` fields, shared or project-specific, in a vault the executing reader already has approved access to. Do not duplicate a private key or broaden its grant to add a caller.
- `STANDING_APPROVAL_<ENV>` with its matching `_UNTIL` date: optional; Pablo's scope and expiry.

Before reusing an App, verify its registered dispatch job, its permissions (Actions write, Contents read, Metadata read) and the installation's approved repository set. The item must identify the installation for the account that owns `REPO`; another account's installation ID is not interchangeable. An Actions-only callback identity is reusable only if its reviewed contract also admits this caller and deploy workflow; it grants no tag-writing authority.

Token scope: the mint helper requests an installation token without a repository restriction, and the later repository check proves only that the token can see `REPO`, not that it is limited to it. Shared installation access must be explicitly accepted; stop if the caller requires a narrower token boundary.

New Apps, installations, repository access, credential items and reader grants each need Pablo's authorization; project setup does not imply it. With no compatible reviewed identity or item, prepare that decision first.

## Failure modes

- Tag push refused: the pusher is not a repository administrator, or the version already exists. Pick the next version; never force.
- Release verification fails: staging has no record for that commit, or its artifact was rebuilt. Release a commit staging did record, after Pablo confirms which.
- `op read` prompts for approval (desktop auth, unless a release-agent service account token is exported): Pablo approves in 1Password. It is a desk-bound approval, so check the presence signal: at his desk, ask in chat; away or unknown, also notify once. Wait rather than retry.
- 403 on dispatch: the app is not installed on the repo or lacks `actions: write`.
- No `--approval` and no standing grant for production: the script stops before touching anything, by design.
- Run not found after dispatch: wait 10 seconds and list runs for the workflow; never dispatch twice.
