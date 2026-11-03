---
name: onepassword-project-setup
description: Put a project on Pablo's 1Password reference model. Use when starting a new project, adopting an existing repo, or converting a .env or GitHub Actions secrets to op:// references. Creates the project's Dev/Prod vaults, per-consumer service accounts, a reference-only .env.op from the current .env (unmatched secrets become items), automatic direnv loading, and the GitHub Actions load-secrets step. Not for production secrets that only exist in GitHub (those need items first) and never prints secret values.
---

# 1Password project setup

Model: one vault per project per tier, one service account per consumer, every consumer holds exactly one bootstrap credential, everything else is an `op://` reference.

| Tier | Vault | Readable by | Holds |
| --- | --- | --- | --- |
| Dev | `<Project> Dev` | `sa-<project>-local` (local agents), `sa-<project>-ci` (GitHub Actions) | ci / dev / staging / local credentials; environments are items, not vaults |
| Prod | `<Project> Prod` | `sa-<project>-release` only (GitHub `production` environment) | production keys, release authority, App Store Connect team key, GitHub App for deploys |
| Shared infra | `Indie Infra Dev` / `Indie Infra Prod` | the matching project accounts when needed | Cloudflare, Resend, Azure, Terraform backend, shared Apple signing identity |
| Agent tools | `Agent Tools Dev` | local service accounts | cross-project keys agents use (Poke, Kagi, personal LLM keys) |

Names: items `<Provider> <Project>-<env>` or `<Project> local <purpose>`; tags `project:<slug>`, `env:<dev|ci|staging|local|prod|runtime>`, `consumer:<local|ci|release|runtime>`. Item titles must not contain `·`, `/`, or parentheses: secret references reject them (reference by item ID otherwise). Service accounts: `sa-<project>-<consumer>`, 89-day expiry from the CLI (the maximum), tokens recorded in the human-only `SA Tokens` vault with grants, consumer, deploy location, expiry.

## Files in this skill

| File | Use |
| --- | --- |
| `scripts/build-env-op.py` | Builds `.env.op` from an existing `.env`; creates items for unmatched credentials. |
| `scripts/store-sa-token.sh` | Stores a service-account token as an `SA Tokens` item from stdin, without printing it. |
| `scripts/match-env-to-items.py` | Maps a host's plaintext env file to existing items by value hash; prints template lines, never values. |
| `scripts/setup-host-agent-env.sh` | Installs the shared-keys renderer on a host: refresh script, launchd or systemd schedule, template stub, shell loader. |
| `templates/env.op.example` | Starting `.env.op` for a project with no `.env`: `op://` references for secrets, literals for config. |
| `templates/op-run.sh` | `op run` wrapper: loads `~/.config/op/sa/<project>-local.token` (refuses a mode other than 0600) and runs `op run --env-file .env.op -- "$@"`. |
| `templates/envrc` | Loads the scoped token and resolves `.env.op` for ordinary project commands through direnv, with a 0600 check and no plaintext environment file. |
| `templates/load-secrets-step.yml` | Standalone GitHub Actions step for a repository outside the indie-infra family: `1password/load-secrets-action` pinned to `70062d7a876d3eb6334754fa26efd2fbd90c32f2` (v5.0.1), CLI 2.41.0, step outputs only. App repositories use the shared composite action instead (step 5). |
| `references/xcode-cloud.md` | Where Xcode Cloud secrets live and which App Store Connect key the Dev vault may hold. |

## Steps for a project

Steps 1 and 3 create access and need Pablo's authorization, but a request that already covers setting the project up on this model ("put PROJECT on the 1Password model", "create the vaults and service accounts for PROJECT") is that authorization: do not ask again per step. Ask only for an access change the request does not cover, such as a service account with a grant outside the three below (grant lists are permanent) or a vault for a project he did not name.

1. **Vaults**: `op vault create "<Project> Dev"` and `"<Project> Prod"` with one-line descriptions saying who reads them.
2. **Items**: move or create the project's credentials in the right tier; tag them. Keep human logins in `Developer Accounts`.
3. **Service accounts** (each grant list is permanent):
   ```bash
   op service-account create sa-<project>-local   --expires-in 89d --vault "<Project> Dev:read_items" --vault "Agent Tools Dev:read_items" --raw
   op service-account create sa-<project>-ci      --expires-in 89d --vault "<Project> Dev:read_items" --raw
   op service-account create sa-<project>-release --expires-in 89d --vault "<Project> Prod:read_items" --raw
   ```
   Add `--vault "Indie Infra Prod:read_items"` to the release account only when that project's deploy reads shared providers (Cloudflare, Resend, Azure); grants are permanent, so decide before creating.
   Capture each `--raw` token into a variable, write the local one to `~/.config/op/sa/<project>-local.token` (0600), upload ci/release with `gh secret set OP_SERVICE_ACCOUNT_TOKEN --env <ci|production> < file`, store all three as items in `SA Tokens` (`scripts/store-sa-token.sh`), then delete the local copies of the ci/release tokens. Never echo a token.
4. **Local .env.op**: with an existing `.env`, `scripts/build-env-op.py --repo <path> --project <slug> --vault "<Project> Dev"` reads it (values stay in-process), matches each credential to an existing item by value hash (single-line fields only), creates `<Project> local <VAR>` items for unmatched credentials, writes `.env.op` with references for credentials and literals for config, and adds `.env.op` and `.envrc` to `.git/info/exclude`. Without a `.env`, copy `templates/env.op.example` to `.env.op`, edit the references, and exclude both files yourself: `for f in .env.op .envrc; do grep -qxF "$f" .git/info/exclude || echo "$f" >> .git/info/exclude; done`.

   Install direnv and configure its shell hook once. Create `.envrc` from `templates/envrc`, replace `PROJECT`, inspect it, and run `direnv allow`. Directory entry resolves `.env.op` with the project token; directory exit unloads it. The token file must have mode 0600. Resolved values stay in memory. Normal project commands need no prefix.

   Copy `templates/op-run.sh` into the repository and replace `PROJECT` for noninteractive launchers. Wrap the agent or server once, rather than resolving secrets for each command; Families accounts have a 1,000-request daily quota. Integrate this into the launcher instead of requiring Pablo to remember a special invocation.
5. **GitHub Actions**: resolve the `op://` references inside the job that uses them and map each value only into the steps that call the provider; never `export-env: true`, never job outputs (GitHub redacts them). Remove the matching `${{ secrets.X }}` lines. The job declares `environment: ci` (only secret: `OP_SERVICE_ACCOUNT_TOKEN`) or `environment: production` (only secret: the release token). App repositories use the shared composite action `load-1password-secrets` in the indie-infra repository, pinned to a commit, which keeps the action and CLI pins in one place:
   ```yaml
         - name: Load secrets from 1Password
           id: op
           uses: OWNER/indie-infra/.github/actions/load-1password-secrets@<commit>
           with:
             service-account-token: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
             secrets: |
               OPENAI_API_KEY=op://PROJECT Dev/OpenAI PROJECT-ci/credential
         - name: Run the tests
           env:
             OPENAI_API_KEY: ${{ fromJSON(steps.op.outputs.secrets).OPENAI_API_KEY }}
   ```
   A repository with no shared infrastructure uses `templates/load-secrets-step.yml` directly (same pins, values as `steps.op.outputs.<NAME>`).
6. **Deploys by agents**: if the project has a deploy workflow, create its GitHub App and config per the `github-release-dispatch` skill. Apple projects built by Xcode Cloud: follow `references/xcode-cloud.md` (Xcode Cloud keeps its own secret variables; the Dev vault holds only a Developer-role key for triggering builds).
7. **Verify**: in a fresh shell with provider variables cleared and biometric unlock disabled, enter the project and verify its normal start command inherits resolved values. Leave the directory and verify they unload. Never print the values. `scripts/op-run.sh sh -c 'env | grep -q op://; [ $? -eq 1 ]'` exits 0 only when no reference is left unresolved: grep status 1 means no match, 0 means an unresolved reference remains, and 2 or higher means grep itself failed, so only status 1 counts as success (a bare `! grep` would also turn a grep error into success); run the test suite through the wrapper; open a PR for the workflow change and let CI prove it.
8. **Record**: tick the project in the plan document; add a task reminder for the service-account expiry (about five days before).

## When a project does not get service accounts

1Password stays the value store in every case; only the consumer side differs.

| Case | Why | What runs instead |
| --- | --- | --- |
| App built and signed by Xcode Cloud, released through GitHub environments | `op` may not be a build or runtime dependency, and Xcode Cloud reads only its own variables | Projection: items in `<Project> Prod`, re-projected into the GitHub environment secrets (`gh secret set`, value over stdin). No `sa-<project>-*` accounts. |
| Long-running service on a host | 1Password must not be in the boot path | A `sa-<project>-runtime` token file on the host (0600) and a scheduled refresh that renders the env file from the runtime vault; the service reads the file from disk. |
| Any host's shell and agents (personal keys) | The desktop app's CLI integration needs an unlocked GUI session, and shells must not prompt | A host-scoped `sa-<host>-agents` token that renders one env file on a schedule; see Shared keys on a host. Plain SSH keys for the agent routes. |
| Repository whose only secret is an agent OAuth token | Nothing project-specific to protect | One shared agents vault and service account for all such repositories, exposed as a repository secret the workflows pass to the composite action. |
| Recovery material (signing identities, profiles, encryption keys, the plaintext `.env` kept until every check passes) | Needed when the automated path is broken | Prod or human-only vault, never granted to a Dev or CI account; the plaintext `.env` goes only after step 7 passes for every consumer. |

## Shared keys on a host

Personal keys used on every host and by every agent (model providers, task, notes and bookmark apps) are host- and consumer-agnostic: one item per provider in the agent tools vault, titled `<Provider> API`, never by host or consumer. Each host reads them with its own service account and renders one 0600 file; shells source that file and never call 1Password, so login shells, scripts and SSH commands work with the app locked. A key that can mint other credentials (for example a token-creator token) stays in the human-only vault and out of the rendered file.

1. **Inventory.** `scripts/match-env-to-items.py` (defaults to `~/.zshenv.local`) prints each secret-looking variable as a ready template line, `NAME=op://<vault>/<item-id>/<field>  # <title>`, or `NAME=NO 1PASSWORD ITEM`. Values never print; matching is by hash, so a stale or rotated value shows as missing.
2. **Items.** Store each unmatched value as an item (JSON on stdin, parity checked by hash), or point the variable at the current item when the host only holds an old copy.
3. **Identity.** Pablo creates the account; grants are permanent: `op service-account create sa-<host>-agents --expires-in 89d --vault "<agent tools vault>:read_items" --raw > ~/.config/op/sa/<host>-agents.token` (under `umask 077`; add a runtime vault only if a host value lives there), then records it with `scripts/store-sa-token.sh`.
4. **Install.** `scripts/setup-host-agent-env.sh --alias <host>` writes `~/.local/bin/refresh-agent-env`, a launchd agent or systemd user timer (at login and every six hours), the template stub `~/.config/op/env/<host>-agent.env.tpl` and the loader block in `~/.zshenv.local`. Paste the inventory lines into the template and run `refresh-agent-env`; it refuses to replace the rendered file if any reference is unresolved.
5. **Cut over.** Back up `~/.zshenv.local` (0600), remove the assignments the template now covers, keep the non-secret exports, check a fresh `zsh -l -c` sees every name, then delete the backup with `rm -P`. Never export a service-account token into shells.

The template is the host's inventory of secret variables; `env | cut -d= -f1 | sort` in a new shell shows what is exported. Running processes keep the environment they started with until they restart.

## Gotchas

- Always run `build-env-op.py --dry-run` first and read the list: a stale value in `.env` (e.g. a rotated key) will not match its item and would become a duplicate item; fix `.env` or hand-edit the reference instead.
- Output paths must be relative to the selected repository, with existing real parent directories. The helper rejects symlinks, hardlinks, and non-regular output or exclusion files before contacting 1Password, including during dry-run. Writes replace files atomically with mode 0600; linked worktrees continue to leave shared Git exclusions alone. Treat generated dotenv literals as data for `op run`, never as a shell script.

- `op item move` and `op item create` read stdin: in loops, append `</dev/null`.
- `op run` masks any output that contains a secret value; a short local password like a username word mangles test output. Use `--no-masking` for test runs or choose distinctive local credentials.
- Tests that assert "variable unset" defaults will fail under `op run` when `.env.op` sets that variable; that is the same as sourcing `.env`.
- SSH Key items cannot be edited from the CLI; Server items reject `--url`; items with passkeys cannot be moved from the CLI.
- Required reviewers on private-repo environments need GitHub Enterprise; use a dispatch gate instead.
