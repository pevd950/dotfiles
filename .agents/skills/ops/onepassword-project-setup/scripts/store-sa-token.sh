#!/usr/bin/env bash
# Store a freshly created service-account token as an item in the SA Tokens vault, without printing it
# and without putting it in a process argument: the item is sent to `op item create -` as JSON on stdin.
# Usage: store-sa-token.sh <sa-name> <project> <consumer> "<grants text>" "<deployed-to text>" < token-on-stdin
# Example: op service-account create sa-foo-ci --expires-in 89d --vault "Foo Dev:read_items" --raw \
#            | store-sa-token.sh sa-foo-ci foo ci "Foo Dev: read_items" "GitHub OWNER/foo ci environment"
set -euo pipefail
name="${1:?sa name}"; project="${2:?project}"; consumer="${3:?consumer}"; grants="${4:?grants}"; deployed="${5:?deployed-to}"
token="$(cat)"; [ -n "$token" ] || { echo "no token on stdin" >&2; exit 1; }
exp="$(date -v+89d +%Y-%m-%d 2>/dev/null || date -d '+89 days' +%Y-%m-%d)"
exp_epoch="$(date -v+89d +%s 2>/dev/null || date -d '+89 days' +%s)"
SA_TOKEN="$token" python3 - "$name" "$project" "$consumer" "$grants" "$deployed" "$exp" "$exp_epoch" <<'PY' | op item create - --vault "SA Tokens" --format json | python3 -c 'import json,sys; print("stored in SA Tokens:", json.load(sys.stdin)["title"])'
import json, os, sys
name, project, consumer, grants, deployed, exp, exp_epoch = sys.argv[1:8]
item = {"title": name, "category": "API_CREDENTIAL", "tags": ["service-account", f"project:{project}", f"consumer:{consumer}"],
  "fields": [
    {"id": "credential", "type": "CONCEALED", "label": "credential", "value": os.environ["SA_TOKEN"]},
    {"id": "expires", "type": "DATE", "label": "expires", "value": exp_epoch},
    {"id": "grants", "type": "STRING", "label": "grants", "value": grants},
    {"id": "deployed_to", "type": "STRING", "label": "deployed to", "value": deployed},
    {"id": "rotation", "type": "STRING", "label": "rotation", "value": f"Expires {exp} (CLI max 90d); grants immutable, recreate to change scope"},
  ]}
print(json.dumps(item))
PY
