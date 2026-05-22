---
name: trakt-cli
description: Work with Trakt.tv through the local trakt-cli. Use when Codex needs to verify Trakt access, inspect movies, shows, calendars, recommendations, watchlists, ratings, history, playback, or carefully update authenticated Trakt account state from the command line.
---

# Trakt CLI

## Core Rules

- Use the local CLI directly. Prefer `trakt-cli` from `PATH`.
- These examples target the `trakt-cli` command surface that exposes `configure`, `auth`, `me`, `movies`, `shows`, `recommendations`, and `sync` in `trakt-cli --help`. If a host has a different Trakt CLI package with only commands such as `search`, `history`, `watchlist`, `calendar`, and `progress`, treat it as an unsupported variant for this skill and inspect its help before proceeding.
- Prove access with a live read before claiming Trakt works:

```bash
trakt-cli --help
trakt-cli me --json
trakt-cli sync watchlist --limit 3 --json
```

- Personalized commands require `trakt-cli configure` and `trakt-cli auth`.
- Prefer `--json` for agent work.
- Do not add, remove, rate, check in, scrobble, or mutate Trakt items unless the user explicitly asks for that exact change.
- Resolve titles to a specific Trakt item before any write.

## Setup

Create a Trakt API app at:

```text
https://trakt.tv/oauth/applications/new
```

Use a descriptive app name such as `<host> Codex` or `Local Agent CLI`. For a local/headless CLI flow, use a non-web redirect URI such as:

```text
urn:ietf:wg:oauth:2.0:oob
```

This is the out-of-band PIN-style OAuth flow used by the CLI; after `trakt-cli auth`, follow the printed browser/PIN instructions.

Then configure and authenticate:

```bash
trakt-cli configure --client-id "$TRAKT_CLIENT_ID" --client-secret "$TRAKT_CLIENT_SECRET"
trakt-cli auth
```

## Common Reads

Search and inspect:

```bash
trakt-cli search text movie "The Matrix" --json
trakt-cli search text show "Severance" --json
trakt-cli movies get "the-matrix-1999" --extended full --json
trakt-cli shows get "severance" --extended full --json
```

Browse:

```bash
trakt-cli movies trending --json
trakt-cli shows trending --json
trakt-cli calendars shows --json
trakt-cli calendars premieres --json
```

Personal data:

```bash
trakt-cli sync watchlist --json
trakt-cli recommendations movies --json
trakt-cli sync history --type episodes --json
```

Note: on some `trakt-cli` releases, `sync playback` and `sync last-activities` return `HTTP 405 Method Not Allowed`; avoid using them as health checks until the CLI route is fixed upstream.

## Mutation Guardrails

- Search first when the user gives a title, then pick the matching type/year before writing.
- Use the smallest JSON payload that matches the target item type.
- For destructive operations such as remove, reset, clear, unlike, unfollow, or reorder, state exactly what will change before running the command.

Example watchlist write after resolving a movie ID:

```bash
trakt-cli sync add-watchlist --items '{"movies":[{"ids":{"trakt":603}}]}' --json
```

## Response Style

- Mention the resolved title, media type, and year when available.
- Summarize the result instead of dumping raw JSON unless requested.
- For writes, state exactly what changed.
