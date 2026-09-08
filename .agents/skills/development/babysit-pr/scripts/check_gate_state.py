#!/usr/bin/env python3
"""Assess classified check snapshots, without GitHub access or side effects."""

import hashlib
import json
import sys


def assess(snapshot):
    """Return CI evidence and escalation state; never certify merge readiness."""
    head = snapshot["head_sha"]
    now = snapshot["now"]
    if snapshot["state"] in ("MERGED", "CLOSED"):
        return {"decision": "stop", "notify": False, "diagnose": [], "checkpoint": None}
    if snapshot["state"] != "OPEN":
        raise ValueError("Unknown PR state")

    blockers = []
    diagnose = []
    known_queue_starts = []
    if snapshot.get("rules_verified") is not True:
        blockers.append({"id": "rules", "status": "unverified"})
    for check in snapshot["checks"]:
        kind = check["classification"]
        if kind not in ("required", "evidence", "duplicate"):
            raise ValueError("Unknown check classification")
        status = check["status"]
        current = check["head_sha"] == head
        if (current and status == "queued" and check.get("jobs") == 0
                and now - check.get("queued_since", now) >= 15 * 60):
            diagnose.append(check["id"])
        if kind == "duplicate":
            if not check.get("reason"):
                raise ValueError("Duplicate requires a verified rationale")
            continue
        passed = status == "success" or (
            status in ("neutral", "skipped") and check.get("skip_allowed") is True
        )
        if kind == "required":
            blocked = not current or not passed
        else:
            # Stale evidence cannot satisfy policy but also cannot diagnose this head.
            blocked = current and not passed and status not in ("queued", "in_progress")
        if blocked:
            if current and status == "queued" and "queued_since" in check:
                known_queue_starts.append(min(now, check["queued_since"]))
            blockers.append({
                "id": check["id"], "status": status if current else "stale",
                "attempt": check.get("attempt"), "jobs": check.get("jobs"),
            })

    if not blockers:
        return {"decision": "checks_satisfied", "notify": False,
                "diagnose": sorted(diagnose), "checkpoint": None}
    blockers.sort(key=lambda check: check["id"])
    fingerprint = hashlib.sha256(json.dumps(
        [head, snapshot.get("policy_id"), blockers], sort_keys=True
    ).encode()).hexdigest()
    previous = snapshot.get("previous") or {}
    same = previous.get("state_fingerprint") == fingerprint
    since = previous["blocked_since"] if same else now
    if not previous and known_queue_starts:
        # A first observation of an already stalled run must not buy it 30 more minutes.
        since = min(known_queue_starts)
    polls = previous["unchanged_polls"] + 1 if same else 0
    notified = previous.get("last_notified_at") if same else None
    checkpoint = {
        "head_sha": head, "blocking_gate": [check["id"] for check in blockers],
        "blocked_since": since, "state_fingerprint": fingerprint,
        "unchanged_polls": polls, "last_notified_at": notified,
    }
    return {"decision": "blocked", "diagnose": sorted(diagnose),
            "notify": notified is None and (now - since >= 30 * 60 or polls >= 2),
            "checkpoint": checkpoint}


if __name__ == "__main__":
    print(json.dumps(assess(json.load(sys.stdin)), sort_keys=True))
