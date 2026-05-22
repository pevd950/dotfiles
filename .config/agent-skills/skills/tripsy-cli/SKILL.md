---
name: tripsy-cli
description: Work with Tripsy travel data through the local Tripsy CLI. Use when Codex needs to verify Tripsy access, inspect trips, list or update trip activities, lodging, transport, expenses, collaborators, inbox items, documents, or plan/write Tripsy itineraries from the command line instead of relying on the remote Tripsy MCP.
---

# Tripsy CLI

## Core Rules

- Use the local CLI directly. Prefer `$HOME/.local/bin/tripsy`; if unavailable, check `command -v tripsy`.
- Prove access with a live read before claiming Tripsy works:

```bash
"$HOME/.local/bin/tripsy" doctor
"$HOME/.local/bin/tripsy" auth status --json
```

- Treat the remote Tripsy MCP as optional. Prefer the CLI when the remote MCP is configured but does not expose tools or has session/auth instability.
- Prefer `--json` for agent work. Use `--quiet` when you need raw JSON data only.
- Do not create, update, delete, upload, or attach Tripsy resources unless the user asked for that exact mutation.
- Tripsy stores the CLI token in Keychain by default. If a scheduled/noninteractive run loses auth, check `tripsy doctor` and ask the user to re-run CLI auth rather than inventing a token.

## Common Reads

Current user:

```bash
"$HOME/.local/bin/tripsy" me show --json
```

Trips:

```bash
"$HOME/.local/bin/tripsy" trips list --json
"$HOME/.local/bin/tripsy" trips following --json
"$HOME/.local/bin/tripsy" trips show <trip-id> --json
```

Trip details:

```bash
"$HOME/.local/bin/tripsy" activities list --trip <trip-id> --json
"$HOME/.local/bin/tripsy" hostings list --trip <trip-id> --json
"$HOME/.local/bin/tripsy" transportations list --trip <trip-id> --json
"$HOME/.local/bin/tripsy" expenses list --trip <trip-id> --json
"$HOME/.local/bin/tripsy" collaborators --trip <trip-id> --json
```

Agent command catalog:

```bash
"$HOME/.local/bin/tripsy" commands --json
"$HOME/.local/bin/tripsy" trips --help --agent
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
- Use exact ISO-8601 UTC datetimes for timed items plus the local `timezone`.
- Set `latitude` and `longitude` for location-based activities, lodging, and transport when available.
- Use `hostings` for lodging, `transportations` for point-to-point movement, and `activities` for stops/events/meals.
- Choose the most specific supported category slug. If unsure, run command help with `--agent` before mutating.
- Prefer a direct `images.unsplash.com/photo-...` URL for trip covers, not an Unsplash page URL.
