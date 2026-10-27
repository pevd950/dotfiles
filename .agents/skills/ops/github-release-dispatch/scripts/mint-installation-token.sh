#!/usr/bin/env bash
# Mint a GitHub App installation token from a 1Password item.
# Usage: mint-installation-token.sh "op://Vault/Item"   (item fields: app_id, installation_id, private_key)
# Prints the token to stdout. Nothing else is printed to stdout; diagnostics go to stderr.
set -euo pipefail
item="${1:?usage: mint-installation-token.sh 'op://Vault/Item'}"

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

app_id="$(op read "$item/app_id")"
inst_id="$(op read "$item/installation_id")"
key="$(op read "$item/private_key")"

now=$(date +%s)
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' "$((now-30))" "$((now+540))" "$app_id" | b64url)
sig=$(printf '%s.%s' "$header" "$payload" | openssl dgst -sha256 -sign <(printf '%s\n' "$key") -binary | b64url)
jwt="$header.$payload.$sig"

# The bearer JWT goes to curl as a config file on stdin (-K -), never as a process argument.
resp=$(curl -fsS --connect-timeout 10 --max-time 60 -X POST -K - -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/$inst_id/access_tokens" <<CFG
header = "Authorization: Bearer $jwt"
CFG
) || { echo "token request failed" >&2; exit 1; }
tok=$(printf '%s' "$resp" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["token"])')
exp=$(printf '%s' "$resp" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("expires_at",""))')
echo "installation token minted for app $app_id, installation $inst_id, expires $exp" >&2
printf '%s' "$tok"
