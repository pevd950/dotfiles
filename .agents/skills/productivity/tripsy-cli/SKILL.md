---
name: tripsy-cli
description: Work with Tripsy travel data through the local Tripsy CLI. Use when Codex needs to verify Tripsy access, inspect trips, list or update trip activities, lodging, transport, expenses, collaborators, inbox items, documents, or plan/write Tripsy itineraries from the command line instead of relying on the remote Tripsy MCP.
---

# Tripsy CLI

## Core rules

- Prefer `$HOME/.local/bin/tripsy`, falling back to `command -v tripsy`. Treat the remote Tripsy MCP as optional — prefer the CLI when the MCP does not expose tools or has session/auth instability.
- Prove access before claiming Tripsy works: `"$TRIPSY_BIN" doctor` and `"$TRIPSY_BIN" auth status --json`.
- Prefer `--json` for agent work; `--quiet` for raw JSON only.
- No create/update/delete/upload/attach unless the user asked for that exact mutation.
- The CLI token lives in Keychain by default. If a scheduled or noninteractive run loses auth, check `doctor` and ask the user to re-run CLI auth — never invent a token.

## Common reads

```bash
"$TRIPSY_BIN" me show --json
"$TRIPSY_BIN" trips list --json           # also: trips following, trips show <trip-id>
"$TRIPSY_BIN" activities list --trip <trip-id> --json
"$TRIPSY_BIN" hostings list --trip <trip-id> --json
"$TRIPSY_BIN" transportations list --trip <trip-id> --json
"$TRIPSY_BIN" expenses list --trip <trip-id> --json
"$TRIPSY_BIN" collaborators list --trip <trip-id> --json
"$TRIPSY_BIN" commands --json             # agent command catalog; also <cmd> --help --agent
```

List responses are objects with `results`, `count`, `next`, `previous` — not a top-level array.

## Travel signal use

For planning or assistant-summary workflows, use Tripsy as bounded travel context, not a full itinerary dump: surface travel only when it changes the day or week — active/upcoming dated trips, inbox items needing handling, lodging/flight/document gaps, near-term planning decisions. Prefer trip names, dates, destination/timezone, collaborator count, and the next concrete missing piece. If Tripsy is unavailable, mention the gap only when travel context materially matters.

## Itinerary mutation guardrails

- One Tripsy item per actual stop, reservation, meal, tour, or activity — never a whole day in one activity.
- Timed items use exact UTC ISO-8601 with trailing `Z` (`2026-06-01T14:00:00Z`). The IANA `timezone` field is display/localization only — never a second authoritative time to convert again.
- Set `latitude`/`longitude` for location-based items when available.
- `hostings` for lodging, `transportations` for point-to-point movement, `activities` for stops/events/meals. Choose the most specific supported category slug; check `--agent` help before mutating if unsure.
- Trip covers: use a direct `images.unsplash.com/photo-...` URL, not an Unsplash page URL.
