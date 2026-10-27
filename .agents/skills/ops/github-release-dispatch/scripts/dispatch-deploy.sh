#!/usr/bin/env bash
# Dispatch a project's deploy workflow with its GitHub App identity, watch it, log it.
# Usage: dispatch-deploy.sh <project> <environment> [image-tag] [--approval "<Pablo's go, verbatim with time>"] [--ref <ref>] [--no-watch]
# Production requires --approval and (if GATE_VAR is set) the repository variable to be/become true.
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
project="${1:?usage: dispatch-deploy.sh <project> <environment> [image-tag] [--approval TEXT] [--ref REF]}"; shift
environment="${1:?environment required (staging|production)}"; shift
tag=""; approval=""; ref=""; watch=1
while [ $# -gt 0 ]; do
  case "$1" in
    --approval) approval="$2"; shift 2;;
    --ref) ref="$2"; shift 2;;
    --no-watch) watch=0; shift;;
    --*) echo "unknown option $1" >&2; exit 2;;
    *) tag="$1"; shift;;
  esac
done
cfg="${RELEASE_DISPATCH_CONFIG_DIR:-$HOME/Developer/indie-infra/control-plane/apps}/$project/release-dispatch.env"
[ -r "$cfg" ] || { echo "no release-dispatch manifest for $project at $cfg (set RELEASE_DISPATCH_CONFIG_DIR or add it to indie-infra control-plane/apps)" >&2; exit 2; }
# shellcheck disable=SC1090
source "$cfg"
ref="${ref:-$DEFAULT_REF}"
log_dir="$HOME/.local/state/github-release-dispatch"; mkdir -p "$log_dir"; log="$log_dir/deploys.log"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

if [ "$environment" = "$PROD_ENV_NAME" ]; then
  [ -n "$approval" ] || { echo "production needs --approval \"<Pablo's explicit go for this deploy>\"" >&2; exit 3; }
  [ -n "$tag" ] || { echo "production needs an explicit image tag (use resolve-image-tag.sh)" >&2; exit 3; }
fi

# 1. identity: short-lived installation token, env only
GH_TOKEN="$("$S/scripts/mint-installation-token.sh" "$OP_APP_ITEM")"; export GH_TOKEN
gh api /installation/repositories -q '.repositories[].full_name' | grep -qx "$REPO" || { echo "app token cannot see $REPO" >&2; exit 4; }

# 2. production gate variable (set with Pablo's own gh auth, not the app token)
gate_set_by_us=0
if [ "$environment" = "$PROD_ENV_NAME" ] && [ -n "${GATE_VAR:-}" ]; then
  current=$(env -u GH_TOKEN gh variable get "$GATE_VAR" -R "$REPO" 2>/dev/null || echo "")
  if [ "$current" != "true" ]; then
    env -u GH_TOKEN gh variable set "$GATE_VAR" -R "$REPO" --body true >/dev/null || { echo "could not set $GATE_VAR; ask Pablo to set it to true in GitHub" >&2; exit 5; }
    gate_set_by_us=1; echo "$GATE_VAR set to true for this deploy (will be reset)" >&2
  fi
fi
reset_gate() { if [ "$gate_set_by_us" = 1 ]; then env -u GH_TOKEN gh variable set "$GATE_VAR" -R "$REPO" --body false >/dev/null 2>&1 && echo "$GATE_VAR reset to false" >&2; fi; }
trap reset_gate EXIT

# 3. dispatch
before=$(gh run list -R "$REPO" --workflow "$WORKFLOW_FILE" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || echo 0)
args=(-f "$ENV_INPUT=$environment"); [ -n "$tag" ] && args+=(-f "$TAG_INPUT=$tag")
gh workflow run "$WORKFLOW_FILE" -R "$REPO" --ref "$ref" "${args[@]}"
echo "$(stamp) DISPATCH project=$project env=$environment tag=${tag:-latest} ref=$ref approval=\"${approval:-n/a}\"" >> "$log"

# 4. find the run
run_id=""
for _ in 1 2 3 4 5 6; do
  sleep 5
  run_id=$(gh run list -R "$REPO" --workflow "$WORKFLOW_FILE" --event workflow_dispatch --limit 1 --json databaseId,createdAt -q '.[0].databaseId' 2>/dev/null || echo "")
  [ -n "$run_id" ] && [ "$run_id" != "$before" ] && break
  run_id=""
done
[ -n "$run_id" ] || { echo "dispatched, but could not find the new run; check https://github.com/$REPO/actions/workflows/$WORKFLOW_FILE" >&2; exit 0; }
url="https://github.com/$REPO/actions/runs/$run_id"
echo "run: $url"

# 5. watch
if [ "$watch" = 1 ]; then
  gh run watch "$run_id" -R "$REPO" --exit-status >/dev/null 2>&1 && conclusion=success || conclusion=$(gh run view "$run_id" -R "$REPO" --json conclusion -q .conclusion)
  echo "$(stamp) RESULT project=$project env=$environment tag=${tag:-latest} run=$url conclusion=$conclusion" >> "$log"
  echo "conclusion: $conclusion"
  [ "$conclusion" = "success" ] || exit 1
fi
