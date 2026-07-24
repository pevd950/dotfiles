---
name: parcel-cli
description: Work with Parcel package tracking through the official Parcel API. Use when Codex needs to inspect active or recent Parcel deliveries, search Parcel carrier codes, add a package delivery after explicit confirmation, or build package-delivery automations from tracking numbers.
---

# Parcel CLI

## Core rules

- Use the bundled helper: `$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py --help`.
- Auth uses `PARCEL_API_KEY` from the host's local shell exports (such as `~/.zshenv.local`). Never print, paste, commit, or store the key in skill files, repo files, notes, or logs.
- Adding a delivery is an externally visible state change. Run `add` without `--confirm` for dry-run planning; use `--confirm` (optionally `--notify`) only after the user explicitly approves the exact tracking number, carrier code, and description.

## API facts

- Docs: `https://parcelapp.net/help/api.html`. Key goes in the `api-key` HTTP header.
- `POST https://api.parcel.app/external/add-delivery/` — one delivery per request; limit 20 add requests/day including failures; cannot add tracking numbers that require extra input (email, postcode); new deliveries may show no data until Parcel's server updates.
- `GET https://api.parcel.app/external/deliveries/?filter_mode=active|recent`
- `GET https://api.parcel.app/external/supported_carriers.json`

## Common reads

```bash
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" carriers ups
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" deliveries --mode active --summary
"$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py" deliveries --mode recent --json
```

## Adding deliveries

1. Extract candidate tracking numbers from the live source and resolve the carrier code with `carriers`.
2. Check recent/active deliveries for duplicates when practical.
3. Show a compact approval table: tracking number, carrier code/name, description, source.
4. After explicit approval, run `add --confirm`; report successes, failures, and any quota or carrier limitations.

Use `pholder` only for placeholder deliveries.
