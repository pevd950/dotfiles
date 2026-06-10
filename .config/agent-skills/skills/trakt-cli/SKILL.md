---
name: trakt-cli
description: Work with Trakt.tv through the local trakt-cli. Use when Codex needs to verify Trakt access, inspect movies, shows, calendars, recommendations, watchlists, ratings, history, playback, or carefully update authenticated Trakt account state from the command line.
---

# Trakt CLI

## Core Rules

- Use the local CLI directly. Prefer `trakt-cli` from `PATH`.
- These examples target the `trakt-cli` command surface that exposes `configure`, `auth`, `me`, `movies`, `shows`, `recommendations`, `calendars`, and `sync` in `trakt-cli --help`. If a host has a different Trakt CLI package with commands such as `search`, `history`, `watchlist`, `calendar`, and `progress`, treat it as a different supported command surface: inspect its help and translate the workflow instead of applying these examples verbatim.
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
trakt-cli search text "The Matrix" movie --json
trakt-cli search text "Severance" show --json
trakt-cli movies get "the-matrix-1999" --extended full --json
trakt-cli shows get "severance" --extended full --json
```

Note: `trakt-cli 0.1.0` prints `search text <TYPE> <QUERY>` in help, but the
working argument order is `search text <QUERY> <TYPE>`. Verify with a harmless
known title before relying on the generated help text.

Browse:

```bash
trakt-cli movies trending --json
trakt-cli shows trending --json
trakt-cli calendars my-shows --json
trakt-cli calendars all-new-shows --json
```

Personal data:

```bash
trakt-cli sync watchlist --json
trakt-cli recommendations movies --json
trakt-cli sync history --type episodes --json
```

Note: on some `trakt-cli` releases, `sync playback` and `sync last-activities` return `HTTP 405 Method Not Allowed`; avoid using them as health checks until the CLI route is fixed upstream.

## Auth Troubleshooting

If `trakt-cli` returns `HTTP 401 Unauthorized`, distinguish configuration,
OAuth-token, and route failures before asking the user to re-authenticate.
Prefer official CLI auth repair over hand-editing credential files.

1. Confirm client credentials are present without printing values:

```bash
env | sort | awk -F= '/^TRAKT_/ { printf "%s=[SET len=%d]\n", $1, length($2) }'
```

2. Confirm the client ID works for a public API read. This verifies the Trakt
API app credentials independently of the CLI's saved OAuth token:

```bash
tmp=$(mktemp)
code=$(curl -sS -o "$tmp" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -H 'trakt-api-version: 2' \
  -H "trakt-api-key: $TRAKT_CLIENT_ID" \
  'https://api.trakt.tv/shows/trending?limit=1')
printf 'http_code=%s\n' "$code"
test "$code" = 200 || sed -n '1,40p' "$tmp"
rm -f "$tmp"
```

3. If the public API read works but `trakt-cli` still returns 401, the likely
cause is a stale saved OAuth token. Repair it with the CLI first:

```bash
trakt-cli auth
trakt-cli me --json
trakt-cli sync watchlist --limit 3 --json
```

Follow the printed browser/PIN or device-auth instructions. This writes local
credential state, so get explicit user approval before running it unless the
user already asked to repair auth.

4. Inspect saved credential metadata only when diagnosis still needs it. The
macOS config path used by `trakt-cli 0.1.0` is:

```text
~/Library/Application Support/com.trakt.trakt-cli/config.json
```

Do not print token values. It is fine to print key names, lengths, and short
hashes for comparison:

```bash
python3 - <<'PY'
import hashlib, json, os, pathlib
p = pathlib.Path.home() / "Library/Application Support/com.trakt.trakt-cli/config.json"
data = json.loads(p.read_text())
for name, env_name in [("client_id", "TRAKT_CLIENT_ID"), ("client_secret", "TRAKT_CLIENT_SECRET")]:
    saved = data.get(name, "") or ""
    env = os.environ.get(env_name, "") or ""
    fp = lambda s: hashlib.sha256(s.encode()).hexdigest()[:12] if s else "EMPTY"
    print(f"{name}: saved_len={len(saved)} saved_sha12={fp(saved)} env_len={len(env)} env_sha12={fp(env)} match={saved == env}")
for name in ["access_token", "refresh_token"]:
    saved = data.get(name, "") or ""
    fp = lambda s: hashlib.sha256(s.encode()).hexdigest()[:12] if s else "EMPTY"
    print(f"{name}: saved_len={len(saved)} saved_sha12={fp(saved)}")
PY
```

5. Validate after repair:

```bash
trakt-cli me --json
trakt-cli sync watchlist --limit 3 --json
trakt-cli sync watched shows --json --limit 3
```

Manual refresh-token repair is a last resort, not the default skill path. Use it
only after explicit approval, only if `trakt-cli auth` is unavailable or broken,
and keep the detailed repair script in private/local runbook context rather
than this public dotfiles skill. If live auth is unavailable but a local Trakt
export exists, use that export only as a dated fallback and clearly state that
it is not live.

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
