---
name: tripsy-cli
description: Work with Tripsy travel data through the local Tripsy CLI. Use when Codex needs to verify Tripsy access, inspect trips, list or update trip activities, lodging, transport, expenses, collaborators, inbox items, documents, or plan/write Tripsy itineraries from the command line instead of relying on the remote Tripsy MCP.
---

# Tripsy CLI

## Core Rules

- Use the local CLI directly. Prefer `$HOME/.local/bin/tripsy`; if unavailable, check `command -v tripsy`.
- Prove access with a live read before claiming Tripsy works:

```bash
TRIPSY_BIN="${HOME}/.local/bin/tripsy"
if [ ! -x "$TRIPSY_BIN" ]; then TRIPSY_BIN="$(command -v tripsy)"; fi
"$TRIPSY_BIN" doctor
"$TRIPSY_BIN" auth status --json
```

- Treat the remote Tripsy MCP as optional. Prefer the CLI when the remote MCP is configured but does not expose tools or has session/auth instability.
- Prefer `--json` for agent work. Use `--quiet` when you need raw JSON data only.
- Do not create, update, delete, upload, or attach Tripsy resources unless the user asked for that exact mutation.
- Tripsy stores the CLI token in Keychain by default. If a scheduled/noninteractive run loses auth, check `"$TRIPSY_BIN" doctor` and ask the user to re-run CLI auth rather than inventing a token.

## Common Reads

Current user:

```bash
"$TRIPSY_BIN" me show --json
```

Trips:

```bash
"$TRIPSY_BIN" trips list --json
"$TRIPSY_BIN" trips following --json
"$TRIPSY_BIN" trips show <trip-id> --json
```

Trip details:

```bash
"$TRIPSY_BIN" activities list --trip <trip-id> --json
"$TRIPSY_BIN" hostings list --trip <trip-id> --json
"$TRIPSY_BIN" transportations list --trip <trip-id> --json
"$TRIPSY_BIN" expenses list --trip <trip-id> --json
"$TRIPSY_BIN" collaborators --trip <trip-id> --json
```

Agent command catalog:

```bash
"$TRIPSY_BIN" commands --json
"$TRIPSY_BIN" trips --help --agent
```

The list response is an object with `results`, `count`, `next`, and `previous`; do not assume a top-level array.

## Travel Signal Use

For planning or assistant-summary workflows:

- Use Tripsy as bounded travel context, not as a full itinerary dump.
- Surface travel only when it changes the day or week: active/upcoming dated trips, inbox items needing handling, lodging/flight/document gaps, or near-term planning decisions.
- Prefer trip names, dates, destination/timezone, collaborator count, and the next concrete missing piece.
- If Tripsy is unavailable, mention it as a data gap only when travel context materially matters.

## Itinerary Mutation Guardrails

When the user asks to create or refine an itinerary:

- Create one Tripsy item per actual stop, reservation, meal, tour, or activity; do not combine a whole day into one activity.
- Use exact UTC ISO-8601 datetimes with a trailing `Z` for timed items, such as `2026-06-01T14:00:00Z`.
- Set the local IANA `timezone` field separately for display/localization only; do not treat it as a second authoritative time that should be converted again.
- Set `latitude` and `longitude` for location-based activities, lodging, and transport when available.
- Use `hostings` for lodging, `transportations` for point-to-point movement, and `activities` for stops/events/meals.
- Choose the most specific supported category slug. If unsure, run command help with `--agent` before mutating.
- Prefer a direct `images.unsplash.com/photo-...` URL for trip covers, not an Unsplash page URL.
