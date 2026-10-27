#!/usr/bin/env bash
# Store a freshly created service-account token as an item in the SA Tokens vault, without printing it.
# Usage: store-sa-token.sh <sa-name> <project> <consumer> "<grants text>" "<deployed-to text>" < token-on-stdin
# Example: op service-account create sa-foo-ci --expires-in 89d --vault "Foo Dev:read_items" --raw \
#            | store-sa-token.sh sa-foo-ci foo ci "Foo Dev: read_items" "GitHub pevd950/foo ci environment"
set -euo pipefail
name="${1:?sa name}"; project="${2:?project}"; consumer="${3:?consumer}"; grants="${4:?grants}"; deployed="${5:?deployed-to}"
token="$(cat)"; [ -n "$token" ] || { echo "no token on stdin" >&2; exit 1; }
exp="$(date -v+89d +%Y-%m-%d 2>/dev/null || date -d '+89 days' +%Y-%m-%d)"
op item create --category "API Credential" --vault "SA Tokens" --title "$name" \
  --tags "service-account,project:$project,consumer:$consumer" \
  "credential=$token" "expires[date]=$exp" "grants[text]=$grants" "deployed to[text]=$deployed" \
  "rotation[text]=Expires $exp (CLI max 90d); grants immutable, recreate to change scope" \
  --format json </dev/null | python3 -c 'import json,sys; print("stored in SA Tokens:", json.load(sys.stdin)["title"])'
