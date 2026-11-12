# Shared keys on a host

Personal keys used on every host and by every agent (model providers, task, notes and bookmark apps) are host- and consumer-agnostic: one item per provider in the agent tools vault, titled `<Provider> API`, never by host or consumer. Each host reads them with its own service account and renders one 0600 file. Shells source that file and never call 1Password, so login shells, scripts and SSH commands work with the app locked. A key that can mint other credentials (for example a token-creator token) stays in the human-only vault and out of the rendered file.

Script paths are relative to the skill root.

1. **Inventory.** `scripts/match-env-to-items.py` (defaults to `~/.zshenv.local`) prints each secret-looking variable as a ready template line, `NAME=op://<vault>/<item-id>/<field>  # <title>`, or `NAME=NO 1PASSWORD ITEM`. Matching is by value hash, so a stale or rotated value shows as missing.
2. **Items.** Store each unmatched value as an item (JSON on stdin, parity checked by hash), or point the variable at the current item when the host only holds an old copy.
3. **Identity.** Create the host account once the request covers shared keys for this host; that request is the authorization, and Pablo's only step is approving the 1Password prompt. Grants are permanent, so ask before adding any vault the request did not name: `op service-account create sa-<host>-agents --expires-in 89d --vault "<agent tools vault>:read_items" --raw > ~/.config/op/sa/<host>-agents.token` (under `umask 077`; add a runtime vault only if a host value lives there). Record it with `scripts/store-sa-token.sh`.
4. **Install.** `scripts/setup-host-agent-env.sh --alias <host>` writes `~/.local/bin/refresh-agent-env`, a launchd agent or systemd user timer (at login and every six hours), the template stub `~/.config/op/env/<host>-agent.env.tpl` and the loader block in `~/.zshenv.local`. Paste the inventory lines into the template and run `refresh-agent-env`. It writes every value single-quoted, so a shell that sources the file reads stored values as data and never runs them, and it keeps the previous file when a reference is unresolved, a value spans several lines, or a template line is not `NAME=reference`.
5. **Cut over.** Back up `~/.zshenv.local` (0600), remove the assignments the template now covers, keep the non-secret exports, check a fresh `zsh -l -c` sees every name, then delete the backup with `rm -P`. Keep the service-account token in its file, never exported into shells.

## Notes

- The template is the host's inventory of secret variables; `env | cut -d= -f1 | sort` in a new shell shows what is exported.
- Running processes keep the environment they started with until they restart.
- A host set up before 12 Nov 2026 has the older renderer, which wrote values unquoted. Rerun `scripts/setup-host-agent-env.sh --alias <host>` there, with `--label` when the scheduled job has a custom label; it replaces the renderer, keeps the token file the host already uses, and leaves the template and the loader as they are.
