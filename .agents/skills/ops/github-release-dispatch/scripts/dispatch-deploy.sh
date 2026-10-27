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

# Standing grants: the manifest may carry STANDING_APPROVAL_<ENV> (Pablo's words, with scope) plus
# STANDING_APPROVAL_<ENV>_UNTIL (a UTC date, YYYY-MM-DD, the last day the grant is valid). Both are required;
# an expired or undated grant is ignored. AGENTS.md: earlier authorization stays valid within its scope.
# Epoch of UTC midnight for a strict YYYY-MM-DD calendar date; empty for anything else (GNU date would otherwise
# accept "" as today and relative words like "tomorrow"; a round trip rejects dates such as 2026-02-30).
to_epoch() {
  local d="$1" e
  printf '%s' "$d" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || return 0
  e=$(date -u -j -f %Y-%m-%dT%H:%M:%SZ "${d}T00:00:00Z" +%s 2>/dev/null || date -u -d "${d}T00:00:00Z" +%s 2>/dev/null) || return 0
  [ "$(date -u -r "$e" +%Y-%m-%d 2>/dev/null || date -u -d "@$e" +%Y-%m-%d 2>/dev/null)" = "$d" ] && printf '%s' "$e"
  return 0
}
if [ -z "$approval" ]; then
  env_upper=$(printf '%s' "$environment" | tr '[:lower:]-' '[:upper:]_'); standing_var="STANDING_APPROVAL_${env_upper}"
  standing="${!standing_var:-}"; until_var="${standing_var}_UNTIL"; until="${!until_var:-}"
  if [ -n "$standing" ]; then
    until_epoch=$(to_epoch "$until")
    if [ -z "$until_epoch" ]; then echo "$standing_var is set but $until_var is missing or not YYYY-MM-DD; grant ignored" >&2
    elif [ "$(date -u +%s)" -ge $((until_epoch + 86400)) ]; then echo "$standing_var expired on $until; grant ignored" >&2
    else approval="standing grant ($standing_var, until $until): $standing"; fi
  fi
fi
if [ "$environment" = "$PROD_ENV_NAME" ]; then
  [ "$watch" = 1 ] || [ -z "${GATE_VAR:-}" ] || { echo "production with a managed gate variable must be watched: --no-watch would reset $GATE_VAR before the run evaluates it" >&2; exit 3; }
  [ -n "$approval" ] || { echo "production needs --approval \"<Pablo's explicit go for this deploy>\" or a STANDING_APPROVAL_$(printf "%s" "$PROD_ENV_NAME" | tr "[:lower:]-" "[:upper:]_") grant in the manifest" >&2; exit 3; }
  [ -n "$tag" ] || { echo "production needs an explicit image tag (use resolve-image-tag.sh)" >&2; exit 3; }
fi

# 1. identities. The caller's own gh authentication (stored credentials or an inherited GH_TOKEN) is kept for the
#    gate variable; the app's short-lived installation token is used only for app-authenticated commands.
CALLER_GH_TOKEN="${GH_TOKEN:-}"
gh_caller() { if [ -n "$CALLER_GH_TOKEN" ]; then GH_TOKEN="$CALLER_GH_TOKEN" gh "$@"; else env -u GH_TOKEN gh "$@"; fi; }
APP_TOKEN="$("$S/scripts/mint-installation-token.sh" "$OP_APP_ITEM")"
gh_app() { GH_TOKEN="$APP_TOKEN" gh "$@"; }
app_repos=$(gh_app api --paginate /installation/repositories -q '.repositories[].full_name')
printf '%s\n' "$app_repos" | grep -qxF "$REPO" || { echo "app token cannot see $REPO" >&2; exit 4; }

# 2. production gate variable (set with Pablo's own gh auth, not the app token)
gate_set_by_us=0
if [ "$environment" = "$PROD_ENV_NAME" ] && [ -n "${GATE_VAR:-}" ]; then
  current=$(gh_caller variable get "$GATE_VAR" -R "$REPO" 2>/dev/null || echo "")
  if [ "$current" != "true" ]; then
    gh_caller variable set "$GATE_VAR" -R "$REPO" --body true >/dev/null || { echo "could not set $GATE_VAR; ask Pablo to set it to true in GitHub" >&2; exit 5; }
    gate_set_by_us=1; echo "$GATE_VAR set to true for this deploy (will be reset)" >&2
  fi
fi
keep_gate=0
reset_gate() {
  [ "$gate_set_by_us" = 1 ] || return 0
  if [ "$keep_gate" = 1 ]; then echo "$GATE_VAR left at true: the run was not confirmed finished. Reset it after the run completes: gh variable set $GATE_VAR -R $REPO --body false" >&2; return 0; fi
  if gh_caller variable set "$GATE_VAR" -R "$REPO" --body false >/dev/null 2>&1; then echo "$GATE_VAR reset to false" >&2
  else echo "WARNING: could not reset $GATE_VAR; run: gh variable set $GATE_VAR -R $REPO --body false" >&2; fi
}
trap reset_gate EXIT

# 3. dispatch. Snapshot existing dispatch runs on this ref first so the new one can be told apart.
list_runs() { gh_app run list -R "$REPO" --workflow "$WORKFLOW_FILE" --event workflow_dispatch --branch "$ref" --limit 20 --json databaseId,createdAt -q "$1" 2>/dev/null || true; }
before_ids=" $(list_runs '.[].databaseId' | tr '\n' ' ') "
dispatched_epoch=$(date -u +%s)
args=(-f "$ENV_INPUT=$environment"); [ -n "$tag" ] && args+=(-f "$TAG_INPUT=$tag")
gh_app workflow run "$WORKFLOW_FILE" -R "$REPO" --ref "$ref" "${args[@]}"
echo "$(stamp) DISPATCH project=$project env=$environment tag=${tag:-latest} ref=$ref approval=\"${approval:-n/a}\"" >> "$log"

# 4. find the run: a workflow_dispatch run on this ref, created at or after the dispatch, not in the snapshot
run_id=""
for _ in 1 2 3 4 5 6 7 8; do
  sleep 5
  while IFS=$'\t' read -r id created; do
    [ -n "$id" ] || continue
    case "$before_ids" in *" $id "*) continue;; esac
    created_epoch=$(date -u -j -f %Y-%m-%dT%H:%M:%SZ "$created" +%s 2>/dev/null || date -u -d "$created" +%s 2>/dev/null || echo 0)
    [ "$created_epoch" -ge $((dispatched_epoch - 60)) ] || continue
    run_id="$id"; break
  done < <(list_runs '.[] | [.databaseId, .createdAt] | @tsv')
  [ -n "$run_id" ] && break
done
[ -n "$run_id" ] || { keep_gate=1; echo "dispatched, but could not find the new run; check https://github.com/$REPO/actions/workflows/$WORKFLOW_FILE" >&2; exit 6; }
url="https://github.com/$REPO/actions/runs/$run_id"
echo "run: $url"

# 5. watch. The gate stays open until the run is confirmed completed; a watch interrupted by a network error,
#    an expired token or Ctrl-C leaves it open with the reset command printed.
if [ "$watch" = 1 ]; then
  keep_gate=1
  gh_app run watch "$run_id" -R "$REPO" --exit-status >/dev/null 2>&1 || true
  IFS=$'\t' read -r status conclusion < <(gh_app run view "$run_id" -R "$REPO" --json status,conclusion -q '[.status, .conclusion] | @tsv' 2>/dev/null || printf 'unknown\tunknown\n')
  if [ "$status" = "completed" ]; then keep_gate=0; else echo "run $run_id is $status, not completed" >&2; fi
  echo "$(stamp) RESULT project=$project env=$environment tag=${tag:-latest} run=$url status=$status conclusion=$conclusion" >> "$log"
  echo "conclusion: $conclusion"
  [ "$status" = "completed" ] && [ "$conclusion" = "success" ] || exit 1
fi
