---
name: parcel-cli
description: Work with Parcel package tracking through the official Parcel API. Use when Codex needs to inspect active or recent Parcel deliveries, search Parcel carrier codes, add a package delivery after explicit confirmation, or build package-delivery automations from tracking numbers.
---

# Parcel CLI

## Core rules

- Use the bundled helper: `$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py --help`.
- Auth uses `PARCEL_API_KEY` from the host's local shell exports (such as `~/.zshenv.local`). Never print, paste, commit, or store the key in skill files, repo files, notes, or logs.
- Adding a delivery is an externally visible state change. Run `add` without `--confirm` for dry-run planning; use `--confirm` (optionally `--notify`) only after the user explicitly approves the exact tracking number, carrier code, description, and any required postcode/email.

## API facts

- Docs: `https://parcelapp.net/help/api.html`. Key goes in the `api-key` HTTP header.
- `POST https://api.parcel.app/external/add-delivery/` — one delivery per request; limit 20 add requests/day including failures; the API supports optional postcode and email fields; new deliveries may show no data until Parcel's server updates. See [Add Delivery](https://parcelapp.net/help/api-add-delivery.html).
- `GET https://api.parcel.app/external/deliveries/?filter_mode=active|recent` — 20 reads/hour; results are cached upstream and do not trigger a carrier refresh. See [Recent & Active Deliveries](https://parcelapp.net/help/api-view-deliveries.html).
- `GET https://api.parcel.app/external/supported_carriers.json`

The bundled helper accepts optional postcode/email through `--carrier-inputs-file /path/to/private.json` or `--carrier-inputs-file -` for stdin and omits their values from dry-run output. Include any required carrier inputs in the exact user approval. Parcel does not document edit/delete/archive or forced-refresh endpoints. Never blindly retry an add after a timeout or lost response; check the app and recent deliveries first.

For a separately installed remote MCP connector, verify fresh client discovery and its write gate before using it. A deployment plan, package install or local CLI success does not prove the remote connector is live. Preserve existing CLI and automation paths.

## Common reads

```bash
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" carriers ups
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" deliveries --mode active --summary
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" deliveries --mode recent --json
```

## Adding deliveries

1. Extract candidate tracking numbers from the live source and resolve the carrier code with `carriers`.
2. Check recent/active deliveries for duplicates when practical.
3. Read optional carrier fields from a private JSON file or stdin (`{"postcode": "...", "email": "..."}`); omit unused keys. Do not pass their values as command arguments or put them in a shell command.
4. Show a compact approval table: tracking number, carrier code/name, description, source, and any supplied postcode/email. Obtain explicit approval of those values before adding the delivery. Keep that approval in the private conversation; do not include these values in logs or public content.
5. After explicit approval, run `add --confirm`; report successes, failures, and any quota or carrier limitations.

Use `pholder` only for placeholder deliveries.
