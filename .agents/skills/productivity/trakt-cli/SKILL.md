---
name: trakt-cli
description: Work with Trakt.tv through the local trakt-cli. Use when Codex needs to verify Trakt access, inspect movies, shows, calendars, recommendations, watchlists, ratings, history, playback, or carefully update authenticated Trakt account state from the command line.
---

# Trakt CLI

## Core rules

- Use `trakt-cli` from `PATH`. These examples target the command surface exposing `configure`, `auth`, `me`, `movies`, `shows`, `recommendations`, `calendars`, and `sync`. If a host has a different Trakt CLI package (commands like `search`, `history`, `watchlist`, `calendar`, `progress`), inspect its help and translate the workflow instead of applying these examples verbatim.
- Prove access with a live read before claiming Trakt works: `trakt-cli me --json`, then `trakt-cli sync watchlist --limit 3 --json`. Personalized commands require `trakt-cli configure` and `trakt-cli auth`.
- Prefer `--json` for agent work.
- Do not add, remove, rate, check in, scrobble, or mutate Trakt items unless the user explicitly asks for that exact change. Resolve titles to a specific Trakt item before any write.

## Setup

Create a Trakt API app at `https://trakt.tv/oauth/applications/new` with a descriptive name (`<host> Codex`) and the out-of-band redirect URI `urn:ietf:wg:oauth:2.0:oob` (PIN-style OAuth used by the CLI). Then `trakt-cli configure --client-id "$TRAKT_CLIENT_ID" --client-secret "$TRAKT_CLIENT_SECRET"` and `trakt-cli auth`, following the printed browser/PIN instructions.

## Common reads

```bash
trakt-cli search text "The Matrix" movie --json
trakt-cli movies get "the-matrix-1999" --extended full --json
trakt-cli shows trending --json
trakt-cli calendars my-shows --json
trakt-cli sync watchlist --json
trakt-cli recommendations movies --json
trakt-cli sync history --type episodes --json
```

Known CLI drift in `trakt-cli 0.1.0`:

- Help prints `search text <TYPE> <QUERY>`, but the working argument order is `search text <QUERY> <TYPE>`. Verify with a harmless known title before relying on generated help text.
- `sync playback` and `sync last-activities` return `HTTP 405 Method Not Allowed` on some releases; do not use them as health checks until fixed upstream.

## Auth troubleshooting

On `HTTP 401`, follow `references/auth-troubleshooting.md`: verify env credentials are set (lengths only, no values), prove the client ID with a public API read, repair a stale OAuth token with `trakt-cli auth` (user approval first — it writes local credential state), and inspect saved credential metadata only via hashes, never printed values.

## Mutation guardrails

Search first when given a title and pick the matching type/year before writing. Use the smallest JSON payload matching the target item type. For destructive operations (remove, reset, clear, unlike, unfollow, reorder), state exactly what will change before running. Example after resolving a movie ID:

```bash
trakt-cli sync add-watchlist --items '{"movies":[{"ids":{"trakt":603}}]}' --json
```

## Response style

Mention the resolved title, media type, and year. Summarize instead of dumping raw JSON. For writes, state exactly what changed.
