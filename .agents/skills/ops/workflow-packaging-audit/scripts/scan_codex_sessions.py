#!/usr/bin/env python3
"""Collect privacy-safe structural evidence from Codex session JSONL files.

The collector is deliberately metadata-first: full prompts, arguments, and
tool output are never emitted by default.  It accepts both active and archived
roots and tolerates interrupted JSONL writes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

TOOL_KEYS = {"tool_call", "custom_tool_call", "tool_result", "custom_tool_call_output"}
SIDE_RE = re.compile(r"guardian|approval|authorize|sidecar", re.I)
REPLAY_RE = re.compile(r"quoted evidence|replayed context|replay", re.I)
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]+|Bearer\s+\S+|password\s*[:=]\s*\S+|secret\s*[:=]\s*\S+)", re.I)
CORRECTION_RE = re.compile(r"\b(no[, ]|not that|incorrect|wrong|correction|actually|instead)\b", re.I)
FRICTION_RE = re.compile(r"\b(retr(y|ied)|retry|failed|failure|error|timeout|workaround|wrong outcome|denied)\b", re.I)


def _time(value: Any) -> dt.datetime | None:
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc)
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _session_id(path: Path, records: list[dict[str, Any]]) -> str:
    for record in records:
        for key in ("session_id", "conversation_id", "thread_id", "id"):
            if isinstance(record.get(key), str) and record[key]:
                return record[key]
    return path.stem


def _record_time(record: dict[str, Any]) -> dt.datetime | None:
    for key in ("timestamp", "created_at", "updated_at", "time"):
        if key in record and (parsed := _time(record[key])):
            return parsed
    return None


def _safe_text(value: Any, limit: int = 240) -> str | None:
    if not isinstance(value, str):
        return None
    value = SECRET_RE.sub("[REDACTED]", value)
    return value[:limit] + ("…" if len(value) > limit else "")


def collect(source_roots: list[Path], checkpoint: dt.datetime | None = None,
            upper_bound: dt.datetime | None = None, exclude: set[str] | None = None,
            max_sessions: int = 500, max_records: int = 5000,
            detail: bool = False) -> dict[str, Any]:
    exclude = exclude or set()
    candidates: dict[str, tuple[Path, list[dict[str, Any]], int]] = {}
    malformed = 0
    for root in source_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            records: list[dict[str, Any]] = []
            try:
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        try:
                            item = json.loads(line)
                            if isinstance(item, dict):
                                records.append(item)
                        except json.JSONDecodeError:
                            malformed += 1
            except OSError:
                continue
            if not records:
                continue
            sid = _session_id(path, records)
            # Archive moves and resumed sessions naturally coalesce by ID.
            old = candidates.get(sid)
            candidates[sid] = (path, (old[1] if old else []) + records, len(records))

    sessions = []
    coverage = {"sessions_seen": len(candidates), "sessions_included": 0,
                "records_scanned": 0, "tool_events": 0, "malformed_lines": malformed,
                "excluded_sidecars": 0, "excluded_replay": 0, "excluded_sessions": 0}
    for sid, (path, records, _) in sorted(candidates.items()):
        if sid in exclude:
            coverage["excluded_sessions"] += 1
            continue
        if SIDE_RE.search(str(path)) or SIDE_RE.search(sid):
            coverage["excluded_sidecars"] += 1
            continue
        events = []
        for record in records:
            when = _record_time(record)
            if checkpoint and when and when <= checkpoint:
                continue
            if upper_bound and when and when > upper_bound:
                continue
            if REPLAY_RE.search(json.dumps(record, ensure_ascii=False)):
                coverage["excluded_replay"] += 1
                continue
            for item in _walk(record):
                kind = item.get("type") or item.get("record_type")
                role = item.get("role")
                text = item.get("text") or item.get("content") or item.get("message")
                semantic = isinstance(text, str) and (role in {"user", "assistant"} or CORRECTION_RE.search(text) or FRICTION_RE.search(text))
                if kind in TOOL_KEYS or any(key in item for key in TOOL_KEYS) or semantic:
                    name = item.get("name") or item.get("tool") or item.get("function")
                    event = {"kind": kind or "tool_event", "name": str(name) if name else None,
                             "timestamp": when.isoformat() if when else None}
                    if semantic:
                        event["kind"] = "user_message" if role == "user" else "workflow_note"
                        event["categories"] = (["user_correction"] if CORRECTION_RE.search(text) else []) + (["tool_friction"] if FRICTION_RE.search(text) else [])
                        event["preview"] = _safe_text(text)
                    elif kind in {"tool_result", "custom_tool_call_output"}:
                        event["categories"] = ["tool_friction"] if FRICTION_RE.search(json.dumps(item, default=str)) else []
                        event["preview"] = _safe_text(text)
                    if detail:
                        event["record_hash"] = hashlib.sha256(
                            json.dumps(item, sort_keys=True, default=str).encode()).hexdigest()[:16]
                    events.append(event)
        if not events:
            continue
        coverage["sessions_included"] += 1
        coverage["records_scanned"] += len(records)
        coverage["tool_events"] += len(events)
        sessions.append({"id": sid, "source": str(path.parent), "events": events[:max_records]})
        if len(sessions) >= max_sessions:
            break
    return {"schema": "codex-evidence-index.v1", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "provenance": {"roots": [str(root) for root in source_roots], "checkpoint": checkpoint.isoformat() if checkpoint else None,
                           "upper_bound": upper_bound.isoformat() if upper_bound else None},
            "coverage": coverage, "sessions": sessions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", action="append", type=Path, required=True)
    parser.add_argument("--checkpoint", type=dt.datetime.fromisoformat)
    parser.add_argument("--upper-bound", type=dt.datetime.fromisoformat)
    parser.add_argument("--exclude-session", action="append", default=[])
    parser.add_argument("--max-sessions", type=int, default=500)
    parser.add_argument("--max-records", type=int, default=5000)
    parser.add_argument("--detail", action="store_true", help="include bounded record hashes")
    parser.add_argument("--authorized", action="store_true", help="explicitly authorize history access")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.authorized:
        parser.error("history scanning requires explicit --authorized invocation")
    result = collect(args.source_root, args.checkpoint, args.upper_bound, set(args.exclude_session),
                     args.max_sessions, args.max_records, args.detail)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
