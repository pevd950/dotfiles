#!/usr/bin/env bash
# Sourced by the release scripts. load_manifest <project> sources the project's
# release-dispatch manifest and sets MANIFEST_SOURCE to where it came from.
#
# The manifest names the deploy target and may carry standing approvals, so it is
# read from indie-infra's reviewed main branch on the remote, never from whatever
# branch the local clone has checked out. RELEASE_DISPATCH_CONFIG_DIR reads a
# directory as it is, for trying a manifest that is still in review; the dispatch
# script refuses that source for production.
# shellcheck disable=SC2034  # MANIFEST_SOURCE is read by the sourcing script
load_manifest() {
  local project="$1" rel="control-plane/apps/$1/release-dispatch.env" cfg clone tmp rev
  if [ -n "${RELEASE_DISPATCH_CONFIG_DIR:-}" ]; then
    cfg="$RELEASE_DISPATCH_CONFIG_DIR/$project/release-dispatch.env"
    [ -r "$cfg" ] || { echo "no release-dispatch manifest for $project at $cfg" >&2; return 2; }
    # shellcheck disable=SC1090
    source "$cfg"
    MANIFEST_SOURCE="unreviewed:$RELEASE_DISPATCH_CONFIG_DIR"
    return 0
  fi
  clone="$HOME/Developer/indie-infra"
  git -C "$clone" rev-parse --git-dir >/dev/null 2>&1 || { echo "no indie-infra clone at $clone to read the manifest from" >&2; return 2; }
  GIT_TERMINAL_PROMPT=0 git -C "$clone" fetch --quiet origin main || {
    echo "could not refresh indie-infra main; refusing to deploy from a manifest that may be stale" >&2; return 2; }
  tmp="$(mktemp)"
  if ! git -C "$clone" show "origin/main:$rel" > "$tmp" 2>/dev/null; then
    rm -f "$tmp"
    echo "no release-dispatch manifest for $project on indie-infra main ($rel); add it through a PR" >&2
    return 2
  fi
  # shellcheck disable=SC1090
  source "$tmp"
  rm -f "$tmp"
  rev="$(git -C "$clone" rev-parse --short origin/main)"
  MANIFEST_SOURCE="indie-infra main@$rev"
}
