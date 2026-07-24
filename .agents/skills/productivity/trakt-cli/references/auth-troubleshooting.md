# Trakt CLI Auth Troubleshooting

On `HTTP 401 Unauthorized`, distinguish configuration, OAuth-token, and route failures before asking the user to re-authenticate. Prefer official CLI auth repair over hand-editing credential files.

1. Confirm client credentials are present without printing values:

```bash
env | sort | awk -F= '/^TRAKT_/ { printf "%s=[SET len=%d]\n", $1, length($2) }'
```

2. Confirm the client ID works for a public API read — this verifies the Trakt API app credentials independently of the CLI's saved OAuth token:

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

3. If the public read works but `trakt-cli` still returns 401, the likely cause is a stale saved OAuth token. Repair with the CLI first — this writes local credential state, so get explicit user approval unless the user already asked for auth repair:

```bash
trakt-cli auth
trakt-cli me --json
trakt-cli sync watchlist --limit 3 --json
```

4. Inspect saved credential metadata only when diagnosis still needs it. The macOS config path used by `trakt-cli 0.1.0` is `~/Library/Application Support/com.trakt.trakt-cli/config.json`. Do not print token values — key names, lengths, and short hashes are fine:

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

5. Validate after repair: `trakt-cli me --json`, `trakt-cli sync watchlist --limit 3 --json`, `trakt-cli sync watched shows --json --limit 3`.

Manual refresh-token repair is a last resort: only after explicit approval, only if `trakt-cli auth` is unavailable or broken, and keep the detailed repair script in private/local runbook context, not this public dotfiles skill. If live auth is unavailable but a local Trakt export exists, use it only as a dated fallback and clearly state that it is not live.
