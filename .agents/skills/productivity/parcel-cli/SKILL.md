---
name: parcel-cli
description: Work with Parcel package tracking through the official Parcel API. Use when Codex needs to inspect active or recent Parcel deliveries, search Parcel carrier codes, add a package delivery after explicit confirmation, or build package-delivery automations from tracking numbers.
---

# Parcel CLI

## Core Rules

- Use the bundled helper script first:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py --help
```

- Auth uses `PARCEL_API_KEY`, expected from the host's local shell exports such as `~/.zshenv.local`.
- Never print, paste, commit, or store the API key in skill files, repo files, notes, or logs.
- Adding a delivery is an externally visible state change in Parcel. Do not run a confirmed add unless the user explicitly approves the exact tracking number, carrier code, and description.
- Use dry-run output for planning and confirmation:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py add \
  --tracking "1Z..." \
  --carrier ups \
  --description "Package description"
```

- Only use `--confirm` after approval:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py add \
  --tracking "1Z..." \
  --carrier ups \
  --description "Package description" \
  --notify \
  --confirm
```

## API Facts

- API docs: `https://parcelapp.net/help/api.html`
- Add endpoint: `POST https://api.parcel.app/external/add-delivery/`
- Deliveries endpoint: `GET https://api.parcel.app/external/deliveries/?filter_mode=active|recent`
- Carrier list: `GET https://api.parcel.app/external/supported_carriers.json`
- API key is sent as the `api-key` HTTP header.
- Add-delivery limit is 20 requests per day, including failed requests.
- Add accepts one delivery per request.
- The API cannot add tracking numbers that require extra input such as email or postcode.
- Newly added deliveries may show no data until Parcel's server updates them.

## Common Reads

Search carriers:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py carriers ups
```

Summarize active deliveries without dumping all event details:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py deliveries --mode active --summary
```

Return JSON when downstream processing matters:

```bash
$HOME/.agents/skills/productivity/parcel-cli/scripts/parcel_api.py deliveries --mode recent --json
```

## Adding Deliveries

1. Extract candidate tracking numbers from the live source.
2. Resolve the carrier code with `carriers`.
3. Check recent or active deliveries for duplicates when practical.
4. Show a compact approval table: tracking number, carrier code/name, description, source.
5. After explicit approval, run `add --confirm`.
6. Report success, failures, and any quota or carrier limitations.

Use `pholder` only for placeholder deliveries.
