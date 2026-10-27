---
name: onepassword-project-setup
description: Put a project on Pablo's 1Password reference model. Use when starting a new project, adopting an existing repo, or converting a .env or GitHub Actions secrets to op:// references. Creates the project's Dev/Prod vaults, per-consumer service accounts, a reference-only .env.op from the current .env (unmatched secrets become items), the .envrc token loader, and the GitHub Actions load-secrets step. Not for production secrets that only exist in GitHub (those need items first) and never prints secret values.
---

# 1Password project setup

Model (decided 2026-10-27, see Craft "1Password Audit and Migration Plan"): one vault per project per tier, one service account per consumer, every consumer holds exactly one bootstrap credential, everything else is an `op://` reference.

| Tier | Vault | Readable by | Holds |
| --- | --- | --- | --- |
| Dev | `<Project> Dev` | `sa-<project>-local` (Broly agents), `sa-<project>-ci` (GitHub Actions) | ci / dev / staging / local credentials; environments are items, not vaults |
| Prod | `<Project> Prod` | `sa-<project>-release` only (GitHub `production` environment) | production keys, release authority, App Store Connect team key, GitHub App for deploys |
| Shared infra | `Indie Infra Dev` / `Indie Infra Prod` | the matching project accounts when needed | Cloudflare, Resend, Azure, Terraform backend, shared Apple signing identity |
| Agent tools | `Agent Tools Dev` | local service accounts | cross-project keys agents use (Poke, Kagi, personal LLM keys) |

Names: items `<Provider> <Project>-<env>` or `<Project> local <purpose>`; tags `project:<slug>`, `env:<dev|ci|staging|local|prod|runtime>`, `consumer:<local|ci|release|runtime>`. Item titles must not contain `·`, `/`, or parentheses: secret references reject them (reference by item ID otherwise). Service accounts: `sa-<project>-<consumer>`, 89-day expiry from the CLI (the maximum), tokens recorded in the human-only `SA Tokens` vault with grants, consumer, deploy location, expiry.

## Steps for a project

Ask before each step that creates access (vaults are cheap; service accounts are immutable).

1. **Vaults**: `op vault create "<Project> Dev"` and `"<Project> Prod"` with one-line descriptions saying who reads them.
2. **Items**: move or create the project's credentials in the right tier; tag them. Keep human logins in `Developer Accounts`.
3. **Service accounts** (each grant list is permanent):
   ```bash
   op service-account create sa-<project>-local   --expires-in 89d --vault "<Project> Dev:read_items" --vault "Agent Tools Dev:read_items" --raw
   op service-account create sa-<project>-ci      --expires-in 89d --vault "<Project> Dev:read_items" --raw
   op service-account create sa-<project>-release --expires-in 89d --vault "<Project> Prod:read_items" --vault "Indie Infra Prod:read_items" --raw
   ```
   Capture each `--raw` token into a variable, write the local one to `~/.config/op/sa/<project>-local.token` (0600), upload ci/release with `gh secret set OP_SERVICE_ACCOUNT_TOKEN --env <ci|production> < file`, store all three as items in `SA Tokens` (`scripts/store-sa-token.sh`), then delete the local copies of the ci/release tokens. Never echo a token.
4. **Local .env.op**: `scripts/build-env-op.py --repo <path> --project <slug> --vault "<Project> Dev"` reads `.env` (values stay in-process), matches each credential to an existing item by value hash (single-line fields only), creates `<Project> local <VAR>` items for unmatched credentials, writes `.env.op` with references for credentials and literals for config, and adds `.env.op` and `.envrc` to `.git/info/exclude`. Write `.envrc` from `templates/envrc` (direnv optional). Run agents with `op run --env-file .env.op -- claude` (wrap the agent process, not each command: the Families quota is 1,000 requests/day).
5. **GitHub Actions**: add the step from `templates/load-secrets-step.yml` to each job that needs secrets, with `op://` references per variable; remove the matching `${{ secrets.X }}` lines; keep `OP_SERVICE_ACCOUNT_TOKEN` as the only secret in the `ci` environment. Production jobs use `environment: production`, whose secret is the release token. Pin `1password/load-secrets-action` by commit SHA (v5.0.1 = `70062d7a876d3eb6334754fa26efd2fbd90c32f2`).
6. **Deploys by agents**: if the project has a deploy workflow, create its GitHub App and config per the `github-release-dispatch` skill.
7. **Verify**: `OP_SERVICE_ACCOUNT_TOKEN=$(cat ~/.config/op/sa/<project>-local.token) op run --env-file .env.op --no-masking -- sh -c 'env | grep -c op://'` must print 0 unresolved; run the test suite under `op run`; open a PR for the workflow change and let CI prove it.
8. **Record**: tick the project in the Craft plan; add a Todoist reminder for the service-account expiry (about five days before).

## Gotchas learned on plato-ai

- Always run `build-env-op.py --dry-run` first and read the list: a stale value in `.env` (e.g. a rotated key) will not match its item and would become a duplicate item; fix `.env` or hand-edit the reference instead.

- `op item move` and `op item create` read stdin: in loops, append `</dev/null`.
- `op run` masks any output that contains a secret value; a short local password like a username word mangles test output. Use `--no-masking` for test runs or choose distinctive local credentials.
- Tests that assert "variable unset" defaults will fail under `op run` when `.env.op` sets that variable; that is the same as sourcing `.env`.
- SSH Key items cannot be edited from the CLI; Server items reject `--url`; items with passkeys cannot be moved from the CLI.
- Required reviewers on private-repo environments need GitHub Enterprise; use a dispatch gate instead.
