#!/usr/bin/env bash
# Print the image tag (sha-<7>) for a project: the head sha of the latest successful build workflow run on <ref>,
# falling back to the ref's current sha. Usage: resolve-image-tag.sh <project> [ref]
set -euo pipefail
project="${1:?usage: resolve-image-tag.sh <project> [ref]}"; ref="${2:-}"
# shellcheck source=load-manifest.sh
source "$(cd "$(dirname "$0")" && pwd)/load-manifest.sh"
load_manifest "$project" || exit $?
ref="${ref:-$DEFAULT_REF}"
sha=""
if [ -n "${BUILD_WORKFLOW_FILE:-}" ]; then
  sha=$(gh run list -R "$REPO" --workflow "$BUILD_WORKFLOW_FILE" --branch "$ref" --status success --limit 1 --json headSha -q '.[0].headSha' 2>/dev/null || true)
fi
if [ -z "$sha" ]; then
  sha=$(gh api "repos/$REPO/commits/$ref" -q .sha)
  if [ -n "${BUILD_WORKFLOW_FILE:-}" ]; then echo "no successful $BUILD_WORKFLOW_FILE run found on $ref; using the ref's head sha (image may not exist yet)" >&2
  else echo "no BUILD_WORKFLOW_FILE configured for $project; using the ref's head sha (image may not exist yet)" >&2; fi
fi
echo "sha-${sha:0:7}"
