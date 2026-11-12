---
name: onepassword-project-setup
description: Put a project on Pablo's 1Password reference model (Dev and Prod vaults, per-consumer service accounts, reference-only .env.op, direnv loading, GitHub Actions load-secrets step). Use when starting a project, adopting a repo, or converting .env or Actions secrets to references.
---

# 1Password project setup

Model: one vault per project per tier, one service account per consumer, every consumer holds exactly one bootstrap credential, everything else is an `op://` reference. Never print secret values: the scripts keep them in-process, and tokens travel by variable, stdin or 0600 file.

Production secrets that exist only in GitHub need 1Password items before this setup can reference them.

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
| `scripts/store-sa-token.sh` | Stores a service-account token from stdin as an `SA Tokens` item. |
| `scripts/match-env-to-items.py`, `scripts/setup-host-agent-env.sh` | Host shared keys: inventory and renderer install. |
| `templates/env.op.example` | Starting `.env.op` for a project with no `.env`: `op://` references for secrets, literals for config. |
| `templates/op-run.sh` | `op run` wrapper: loads `~/.config/op/sa/<project>-local.token` (refuses a mode other than 0600) and runs `op run --env-file .env.op -- "$@"`. |
| `templates/envrc` | direnv loader: scoped token with a 0600 check, resolves `.env.op` with no plaintext environment file. |
| `templates/load-secrets-step.yml` | Standalone GitHub Actions step for a repository outside the indie-infra family: `1password/load-secrets-action` pinned to `70062d7a876d3eb6334754fa26efd2fbd90c32f2` (v5.0.1), CLI 2.41.0, step outputs only. |
| `references/xcode-cloud.md` | Where Xcode Cloud secrets live and which App Store Connect key the Dev vault may hold. |
| `references/host-shared-keys.md` | Personal keys shared by every agent on a host: inventory, host service account, renderer install, cut-over. |

## Steps for a project

Steps 1 and 3 create access and need Pablo's authorization. A request that already covers setting the project up on this model ("put PROJECT on the 1Password model", "create the vaults and service accounts for PROJECT") is that authorization, so run both steps without asking again. Ask only for an access change the request does not cover, such as a service account with a grant outside the three below (grant lists are permanent) or a vault for a project he did not name.

1. **Vaults**: `op vault create "<Project> Dev"` and `"<Project> Prod"` with one-line descriptions saying who reads them.
2. **Items**: move or create the project's credentials in the right tier; tag them. Keep human logins in `Developer Accounts`.
3. **Service accounts** (each grant list is permanent):

   ```bash
   op service-account create sa-<project>-local   --expires-in 89d --vault "<Project> Dev:read_items" --vault "Agent Tools Dev:read_items" --raw
   op service-account create sa-<project>-ci      --expires-in 89d --vault "<Project> Dev:read_items" --raw
   op service-account create sa-<project>-release --expires-in 89d --vault "<Project> Prod:read_items" --raw
   ```

   Add `--vault "Indie Infra Prod:read_items"` to the release account only when that project's deploy reads shared providers (Cloudflare, Resend, Azure); decide before creating.
   Capture each `--raw` token into a variable, write the local one to `~/.config/op/sa/<project>-local.token` (0600), upload ci/release with `gh secret set OP_SERVICE_ACCOUNT_TOKEN --env <ci|production> < file`, store all three as items in `SA Tokens` (`scripts/store-sa-token.sh`), then delete the local copies of the ci/release tokens.
4. **Local .env.op**: with an existing `.env`, `scripts/build-env-op.py --repo <path> --project <slug> --vault "<Project> Dev"` matches each credential to an existing item by value hash (single-line fields only), creates `<Project> local <VAR>` items for unmatched credentials, writes `.env.op` with references for credentials and literals for config, and adds `.env.op` and `.envrc` to `.git/info/exclude`. Without a `.env`, copy `templates/env.op.example` to `.env.op`, edit the references, and exclude both files yourself: `for f in .env.op .envrc; do grep -qxF "$f" .git/info/exclude || echo "$f" >> .git/info/exclude; done`.

   Install direnv and configure its shell hook once. Create `.envrc` from `templates/envrc`, replace `PROJECT`, inspect it, and run `direnv allow`. Entering the directory resolves `.env.op` with the project token (the token file must have mode 0600); leaving unloads it. Normal project commands need no prefix.

   For noninteractive launchers, copy `templates/op-run.sh` to `scripts/op-run.sh` in the repository and replace `PROJECT`. Wrap the agent or server once inside its launcher rather than each command: Families accounts have a 1,000-request daily quota.
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
6. **Deploys by agents**: read the project's shared release contract and existing identity register first. Reuse one GitHub App per job within its reviewed trust boundary; a new project does not imply a new App. Use `github-release-dispatch` only for an admitted dispatch path. Apple projects follow `references/xcode-cloud.md` and their reviewed operation profiles; new keys, grants and projections retain their own approval.
7. **Verify**: in a fresh shell with provider variables cleared and biometric unlock disabled, enter the project and check, without printing them, that its normal start command inherits resolved values, then leave the directory and check they unload. `scripts/op-run.sh sh -c 'env | grep -q op://; [ $? -eq 1 ]'` exits 0 only when no reference is left unresolved (grep status 1 is the only success; a bare `! grep` would also pass a grep error). Run the test suite through the wrapper, then open a PR for the workflow change and let CI prove it.
8. **Record**: tick the project's workboard row, or its plan when setup is part of one; add a task reminder for the service-account expiry (about five days before).

## When a project does not get service accounts

1Password stays the value store in every case; only the consumer side differs.

| Case | Why | What runs instead |
| --- | --- | --- |
| App built and signed by Xcode Cloud, released through GitHub environments | `op` may not be a build or runtime dependency, and Xcode Cloud reads only its own variables | Projection: items in `<Project> Prod`, re-projected into the GitHub environment secrets (`gh secret set`, value over stdin). No `sa-<project>-*` accounts. |
| Long-running service on a host | 1Password must not be in the boot path | A `sa-<project>-runtime` token file on the host (0600) and a scheduled refresh that renders the env file from the runtime vault; the service reads the file from disk. |
| Any host's shell and agents (personal keys) | The desktop app's CLI integration needs an unlocked GUI session, and shells must not prompt | A host-scoped `sa-<host>-agents` token that renders one env file on a schedule; follow `references/host-shared-keys.md`. Plain SSH keys for the agent routes. |
| Repository whose only secret is an agent OAuth token | Nothing project-specific to protect | One shared agents vault and service account for all such repositories, exposed as a repository secret the workflows pass to the composite action. |
| Recovery material (signing identities, profiles, encryption keys, the plaintext `.env` kept until every check passes) | Needed when the automated path is broken | Prod or human-only vault, never granted to a Dev or CI account; the plaintext `.env` goes only after step 7 passes for every consumer. |

## Gotchas

- Run `build-env-op.py --dry-run` first and read the list: a stale value in `.env` (for example a rotated key) matches no item and would become a duplicate item; fix `.env` or hand-edit the reference.
- Output paths must be relative to the selected repository, with existing real parent directories. The helper rejects symlinks, hardlinks, and non-regular output or exclusion files before contacting 1Password, including during dry-run. Writes are atomic with mode 0600; linked worktrees leave shared Git exclusions alone. Generated dotenv literals are data for `op run`, not a shell script.
- `op item move` and `op item create` read stdin: in loops, append `</dev/null`.
- `op run` masks any output that contains a secret value; a short local password like a username word mangles test output. Use `--no-masking` for test runs or choose distinctive local credentials.
- Tests that assert "variable unset" defaults fail under `op run` when `.env.op` sets that variable, as they would when sourcing `.env`.
- SSH Key items cannot be edited from the CLI; Server items reject `--url`; items with passkeys cannot be moved from the CLI.
- Required reviewers on private-repo environments need GitHub Enterprise; use a dispatch gate instead.
