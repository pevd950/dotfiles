#!/usr/bin/env python3
"""Bounded metadata-only Codex index; opt-in detail remains private.

This is a bounded rescan, not a durable incremental collector. Do not advance
an audit checkpoint until source gaps, limits and unreviewed evidence are resolved.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any
import importlib.util

_archive_spec = importlib.util.spec_from_file_location("archive_metadata", Path(__file__).with_name("archive_metadata.py"))
_archive_module = importlib.util.module_from_spec(_archive_spec)
_archive_spec.loader.exec_module(_archive_module)

CALLS = {"function_call", "custom_tool_call", "tool_call"}
RESULTS = {"function_call_output", "custom_tool_call_output", "tool_result"}
SIDECARS = {"guardian", "approval", "approval_reviewer", "authorization", "sidecar"}
CORRECTION = re.compile(r"\b(?:no(?=$|[,\s.!?:;])|not that|incorrect|wrong|correction|actually|instead|already approved|asked me again)\b", re.I)
FRICTION = re.compile(r"\b(?:retry|retried|failed|failure|error|timeout|workaround|denied)\b", re.I)
DENIAL = re.compile(r"\b(?:permission denied|not permitted|approval required|authorization required|denied)\b", re.I)
# Intake uses the same per-kind vocabulary that produces candidate signals.
SIGNAL_PATTERNS = {
    "user_message": (("correction_candidate", CORRECTION), ("friction_candidate", FRICTION)),
    "assistant_message": (("friction_candidate", FRICTION),),
    "tool_result": (("friction_candidate", FRICTION), ("denial_candidate", DENIAL)),
}
# Every indexed record must remain inspectable through bounded detail retrieval.
MAX_RECORD_BYTES = 1024 * 1024
# Shared serialized index ceiling, including JSON indentation and final newline.
MAX_INDEX_BYTES = 8 * 1024 * 1024
EXIT = re.compile(r"(?:exit(?:ed)?(?: with)?(?: code)?|Process exited with code)\s*[:=]?\s*(-?\d+)", re.I)
# Defense in depth for opt-in detail, not publication clearance for private prose.
SECRET = re.compile(r"\b(?:sk-[\w-]+|gh[pousr]_[\w]+|Bearer\s+\S+)|\b(?:password|secret|token|api[_-]?key)[\"']?\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)", re.I)
URL = re.compile(r"(?:https?://|craftdocs://|op://)\S+", re.I)
EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
PRIVATE_KEY = re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|\Z)", re.S)


def _hash(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _time(value: Any) -> dt.datetime | None:
    try:
        if isinstance(value, str):
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return dt.datetime.fromtimestamp(value, dt.timezone.utc)
    except (ValueError, OverflowError, OSError):
        pass
    return None


def _label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value) and not SECRET.search(value):
        return value
    return "opaque:" + _hash(value)[:20]


def _source_class(source: Any) -> str:
    """Inspect only source discriminants, never prompts or tool output."""
    tags: set[str] = set()
    def visit(value: Any, depth: int = 0) -> None:
        if depth > 8:
            return
        if isinstance(value, str):
            tags.add(value.lower())
        elif isinstance(value, dict):
            tags.update(str(key).lower() for key in value)
            for child in value.values():
                if isinstance(child, (dict, str)):
                    visit(child, depth + 1)
    visit(source)
    if tags & SIDECARS:
        return "approval_sidecar"
    if "subagent" in tags or "spawn" in tags:
        return "subagent"
    return "primary" if tags & {"cli", "vscode", "exec", "app_server", "app-server", "mcp"} else "unknown"


def _text(item: dict[str, Any]) -> str:
    value = item.get("content", item.get("text", item.get("message", item.get("output", ""))))
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(part["text"] for part in value if isinstance(part, dict) and isinstance(part.get("text"), str))
    if isinstance(value, dict):
        return _text(value)
    return ""


def _tool_output(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("output")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, RecursionError):
            pass
    return value if isinstance(value, dict) else item


def _tool_text(item: dict[str, Any]) -> str:
    """Preserve arbitrary tool JSON when no recognized text wrapper exists."""
    text = _text(_tool_output(item))
    if text:
        return text
    output = item.get("output", "")
    return output if isinstance(output, str) else json.dumps(output)


def _event(record: dict[str, Any]) -> tuple[dict[str, Any], Any] | None:
    """Decode supported envelopes once; embedded/replayed JSON is never walked."""
    item = record.get("payload") if record.get("type") in ("response_item", "event_msg") else record
    if not isinstance(item, dict):
        return None
    kind = item.get("type")
    if not isinstance(kind, str):
        return None
    if kind in CALLS:
        return {"kind": "tool_call", "name": _label(item.get("name", item.get("tool")))}, item.get("call_id", item.get("id"))
    if kind in RESULTS:
        structured = _tool_output(item)
        status: dict[str, Any] = {}
        exit_code = structured.get("exit_code")
        if isinstance(exit_code, int) and not isinstance(exit_code, bool):
            status["exit_code"] = exit_code
        elif match := EXIT.search(_tool_text(item)):
            status["exit_code"] = int(match.group(1))
            status["exit_code_source"] = "output_text_candidate"
        if isinstance(structured.get("isError"), bool):
            status["is_error"] = structured["isError"]
        signals = [name for name, regex in SIGNAL_PATTERNS["tool_result"] if regex.search(_tool_text(item))]
        return {"kind": "tool_result", "status": status, "signals": signals}, item.get("call_id")
    role = item.get("role") if kind == "message" else {"user_message": "user", "agent_message": "assistant"}.get(kind)
    if role in ("user", "assistant"):
        text = _text(item)
        signals = [name for name, regex in SIGNAL_PATTERNS[role + "_message"] if regex.search(text)]
        return {"kind": role + "_message", "signals": signals}, None
    return None


def _open_source(root: Path, relative: str):
    """Open a regular file below root without following any symlink component."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or ".." in parts:
        raise ValueError("Invalid relative source path")
    directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            child_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise ValueError("Source must be a regular file")
        return os.fdopen(fd, "rb")
    finally:
        os.close(directory_fd)


def collect(source_roots: list[Path], checkpoint: dt.datetime | None = None,
            upper_bound: dt.datetime | None = None, exclude: set[str] | None = None,
            *, source_host: str = "local", max_files: int = 1000,
            max_scan_records: int = 100000, max_bytes: int = 64 * 1024 * 1024,
            max_line_bytes: int = MAX_RECORD_BYTES, max_events: int = 5000,
            max_sessions: int = 500, max_pending_calls: int = 5000,
            max_directory_entries: int = 10000, archive_db: Path | None = None,
            archive_db_roots: list[Path] | None = None, max_archive_bytes: int = 64 * 1024 * 1024,
            max_archive_rows: int = 10000, max_archive_query_steps: int = 1000000) -> dict[str, Any]:
    limits = dict(max_files=max_files, max_scan_records=max_scan_records, max_bytes=max_bytes,
                  max_line_bytes=max_line_bytes, max_events=max_events, max_sessions=max_sessions,
                  max_pending_calls=max_pending_calls, max_directory_entries=max_directory_entries,
                  max_archive_bytes=max_archive_bytes, max_archive_rows=max_archive_rows,
                  max_archive_query_steps=max_archive_query_steps)
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in limits.values()):
        raise ValueError("All limits must be positive integers")
    if max_line_bytes > MAX_RECORD_BYTES:
        raise ValueError("Record limit exceeds detail retrieval ceiling")
    if any(boundary is not None and boundary.tzinfo is None for boundary in (checkpoint, upper_bound)):
        raise ValueError("Window boundaries require an explicit timezone")
    if checkpoint and upper_bound and checkpoint >= upper_bound:
        raise ValueError("Checkpoint must precede upper bound")
    exclude = exclude or set()
    counts = dict(files_discovered=0, files_read=0, directory_entries=0, bytes_read=0,
                  records_read=0, malformed_records=0, incomplete_trailing_records=0,
                  duplicate_records=0, untimestamped_events=0, out_of_window_events=0,
                  excluded_session_files=0, excluded_sidecar_files=0, unsupported_records=0,
                  emitted_events=0, pending_calls_evicted=0)
    gaps: list[dict[str, Any]] = []
    truncated: set[str] = set()
    seen_records: set[tuple[str, str, int]] = set()
    record_events: dict[tuple[str, str, int], dict[str, Any]] = {}
    emitted_event_ids: set[int] = set()
    sessions: dict[str, dict[str, Any]] = {}
    source_files: dict[str, list[dict[str, Any]]] = {}
    calls: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    pairing_events: list[tuple[dt.datetime, str, str, dict[str, Any], bool]] = []
    message_mirrors: dict[tuple[str, str, str, str | None], list[tuple[dt.datetime, str, dict[str, Any]]]] = {}
    stop = False
    archive = (_archive_module.read_archive_metadata(archive_db, archive_db_roots or [], source_roots,
               checkpoint, upper_bound, _open_source, max_bytes=max_archive_bytes,
               max_rows=max_archive_rows, max_query_steps=max_archive_query_steps)
               if archive_db else {"status": "disabled", "rows_read": 0, "gaps": [], "selected": {}})
    archive_seen = set()
    for reason in archive["gaps"]:
        gaps.append({"reason": reason})

    def gap(reason: str, root_index: int, relative_path: str | None = None) -> None:
        # Exception strings may contain source text, credentials or private paths.
        gaps.append({"reason": reason, "root_index": root_index, "relative_path": relative_path})

    def files(root: Path, index: int, directory: Path | None = None, depth: int = 0):
        directory = directory or root
        if depth > 64:
            gap("directory_depth_limit", index)
            return
        entries = []
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if counts["directory_entries"] >= max_directory_entries:
                        truncated.add("max_directory_entries")
                        break
                    counts["directory_entries"] += 1
                    entries.append(entry)
        except OSError:
            gap("directory_unreadable", index, str(directory.relative_to(root)))
            return
        for entry in sorted(entries, key=lambda entry: entry.name):
            path = Path(entry.path)
            try:
                if entry.is_symlink():
                    gap("symlink_skipped", index, str(path.relative_to(root)))
                elif entry.is_dir(follow_symlinks=False):
                    yield from files(root, index, path, depth + 1)
                elif entry.is_file(follow_symlinks=False) and path.suffix == ".jsonl":
                    yield path
            except OSError:
                gap("entry_unreadable", index, str(path.relative_to(root)))

    # Discover within the directory-entry budget before spending the content
    # budget. Modification time is an ordering hint only: it never excludes a
    # file or proves window coverage, including for old resumed/copied sessions.
    candidates = []
    for root_index, requested_root in enumerate(source_roots):
        root = requested_root.resolve()
        if not root.is_dir():
            gap("root_missing_or_not_directory", root_index)
            continue
        for path in files(root, root_index):
            try:
                stamp = path.stat(follow_symlinks=False).st_mtime_ns
            except OSError:
                gap("entry_unreadable", root_index, str(path.relative_to(root)))
                continue
            candidates.append((stamp, root_index, root, path))
    candidates.sort(key=lambda row: (-row[0], row[1], str(row[3])))
    for _, root_index, root, path in candidates:
        if counts["files_discovered"] >= max_files:
            truncated.add("max_files"); stop = True; break
        counts["files_discovered"] += 1
        relative = str(path.relative_to(root))
        sid = None
        archive_selection = archive["selected"].get((root_index, relative))
        source_class = "unknown"
        current_turn = None
        file_occurrences: dict[tuple[str, str], int] = {}
        try:
            if not path.resolve().is_relative_to(root):
                gap("path_outside_root", root_index, relative); continue
            with _open_source(root, relative) as handle:
                counts["files_read"] += 1
                while True:
                    remaining = max_bytes - counts["bytes_read"]
                    if remaining <= 0 or counts["records_read"] >= max_scan_records:
                        truncated.add("max_bytes" if remaining <= 0 else "max_scan_records")
                        stop = True; break
                    offset = handle.tell()
                    raw = handle.readline(min(max_line_bytes + 1, remaining))
                    if not raw:
                        break
                    counts["bytes_read"] += len(raw)
                    if len(raw) > max_line_bytes:
                        gap("oversized_record_file_stopped", root_index, relative)
                        break
                    eof_terminated = not raw.endswith(b"\n")
                    if eof_terminated and len(raw) == remaining:
                        # Reaching the byte cap is not evidence of EOF.
                        truncated.add("max_bytes"); stop = True; break
                    counts["records_read"] += 1
                    try:
                        record = json.loads(raw)
                    except (ValueError, UnicodeDecodeError, RecursionError):
                        if eof_terminated:
                            counts["incomplete_trailing_records"] += 1
                            gap("incomplete_trailing_record", root_index, relative)
                            break
                        counts["malformed_records"] += 1
                        gap("malformed_record", root_index, relative)
                        continue
                    if not isinstance(record, dict):
                        counts["unsupported_records"] += 1; continue
                    if record.get("type") == "session_meta":
                        meta = record.get("payload")
                        if not isinstance(meta, dict) or not isinstance(meta.get("id"), str):
                            gap("invalid_session_metadata", root_index, relative); break
                        if sid is not None and sid != meta["id"]:
                            gap("session_identity_changed", root_index, relative); break
                        sid = meta["id"]
                        if archive_selection:
                            archive_seen.add((root_index, relative))
                            if archive_selection["id"] != sid:
                                gap("archive_database_rollout_identity_mismatch", root_index, relative)
                                archive_selection = None
                        source_class = _source_class(meta.get("source"))
                        if sid in exclude:
                            counts["excluded_session_files"] += 1; break
                        if source_class == "approval_sidecar":
                            counts["excluded_sidecar_files"] += 1; break
                        if source_class == "unknown":
                            gap("unknown_session_source", root_index, relative)
                        provenance = {"root_index": root_index, "relative_path": relative}
                        if provenance not in source_files.setdefault(sid, []):
                            source_files[sid].append(provenance)
                        continue
                    if sid is None:
                        gap("missing_session_metadata", root_index, relative); break
                    if record.get("type") == "turn_context" and isinstance(record.get("payload"), dict):
                        current_turn = record["payload"].get("turn_id")
                    try:
                        canonical_hash = _hash(json.dumps(record, sort_keys=True, separators=(",", ":")))
                        decoded = _event(record)
                    except (ValueError, TypeError, RecursionError):
                        counts["malformed_records"] += 1
                        gap("record_decode_failed", root_index, relative)
                        continue
                    occurrence_key = (sid, canonical_hash)
                    ordinal = file_occurrences.get(occurrence_key, 0) + 1
                    file_occurrences[occurrence_key] = ordinal
                    identity = (sid, canonical_hash, ordinal)
                    reused_event = record_events.get(identity)
                    if identity in seen_records:
                        counts["duplicate_records"] += 1
                        if not archive_selection:
                            continue
                    seen_records.add(identity)
                    if decoded is None:
                        counts["unsupported_records"] += 1; continue
                    event, call_id = decoded
                    if reused_event is not None:
                        event = reused_event
                    when = _time(record.get("timestamp"))
                    if when is None:
                        counts["untimestamped_events"] += 1
                        gap("event_timestamp_missing_or_invalid", root_index, relative); continue
                    if upper_bound and when > upper_bound:
                        counts["out_of_window_events"] += 1; continue
                    ref = {"root_index": root_index, "relative_path": relative,
                           "byte_offset": offset, "byte_length": len(raw), "sha256": _hash(raw)}
                    if reused_event is None and event["kind"] in ("user_message", "assistant_message") and record.get("type") in ("event_msg", "response_item"):
                        # Match opposite envelopes one-for-one. Same-envelope
                        # occurrences always remain separate logical messages.
                        try:
                            payload = record["payload"]
                            message_text = _text(payload)
                            turn_id = payload.get("turn_id", record.get("turn_id", current_turn))
                            message_key = (sid, event["kind"], _hash(message_text),
                                           _hash(str(turn_id)) if turn_id is not None else None)
                        except (ValueError, TypeError, RecursionError):
                            counts["malformed_records"] += 1
                            gap("record_decode_failed", root_index, relative)
                            continue
                        mirrors = message_mirrors.setdefault(message_key, [])
                        envelope = record["type"]
                        match_index = next((i for i, (stamp, other, _) in enumerate(mirrors)
                                            if message_text and other != envelope
                                            and bool(checkpoint and when <= checkpoint) == bool(checkpoint and stamp <= checkpoint)
                                            and abs((when - stamp).total_seconds()) <= 1), None)
                        if match_index is not None:
                            _, _, original = mirrors.pop(match_index)
                            original.setdefault("mirror_source_refs", []).append(ref)
                            original["canonical_sha256s"] = sorted(set(original["canonical_sha256s"]) | {canonical_hash})
                            counts["duplicate_records"] += 1
                            event = original
                            reused_event = original
                        else:
                            mirrors.append((when, envelope, event))
                    record_events[identity] = event
                    if reused_event is None:
                        event.update(timestamp=when.isoformat(), source_ref=ref, canonical_sha256s=[canonical_hash])
                    pair_key = (sid, call_id) if isinstance(call_id, str) else None
                    prior = bool(checkpoint and when <= checkpoint)
                    if reused_event is None and pair_key and event["kind"] in ("tool_call", "tool_result"):
                        pairing_events.append((when, sid, call_id, event, prior))
                    if prior and not archive_selection:
                        counts["out_of_window_events"] += 1; continue
                    if id(event) in emitted_event_ids:
                        if archive_selection:
                            if "session_archived_in_window" not in event["selection_reasons"]:
                                event["selection_reasons"].append("session_archived_in_window")
                            sessions[sid]["archived_at"] = archive_selection["archived_at"]
                        continue
                    if len(sessions) >= max_sessions and sid not in sessions:
                        truncated.add("max_sessions"); stop = True; break
                    if counts["emitted_events"] >= max_events:
                        truncated.add("max_events"); stop = True; break
                    if pair_key:
                        event["correlation_id"] = _hash(source_host + "\0" + sid + "\0" + call_id)
                    if event["kind"] == "tool_result":
                        if not pair_key:
                            event["pairing"] = "missing_call_id"
                    session = sessions.setdefault(sid, {"id": _label(sid), "source_class": source_class, "events": []})
                    event["selection_reasons"] = (["record_activity_in_window"] if not prior else [])
                    if archive_selection:
                        event["selection_reasons"].append("session_archived_in_window")
                        session["archived_at"] = archive_selection["archived_at"]
                    session["events"].append(event)
                    emitted_event_ids.add(id(event))
                    counts["emitted_events"] += 1
        except (OSError, ValueError):
            gap("file_unreadable", root_index, relative)
        if stop:
            break
    # Discovery order is not event order: archive fragments may contain earlier
    # calls than active files. This metadata buffer is bounded by scan limits.
    # Preserve source order for ties; a result discovered first can still pair
    # with a later-discovered call at the same coarse timestamp.
    pairing_events.sort(key=lambda row: row[0])
    tied_results: dict[tuple[str, str], tuple[dt.datetime, dict[str, Any], bool]] = {}
    for when, sid, call_id, event, prior in pairing_events:
        key = (sid, call_id)
        if event["kind"] == "tool_call":
            call = {"name": event["name"], "timestamp": event["timestamp"],
                    "source_ref": event["source_ref"], "before_window": prior}
            tied = tied_results.pop(key, None)
            if tied is not None and tied[0] == when:
                if "selection_reasons" in tied[1]:
                    tied[1].pop("pairing", None)
                    tied[1]["call"] = call
                continue
            calls[key] = call
            calls.move_to_end(key)
            if len(calls) > max_pending_calls:
                calls.popitem(last=False)
                counts["pending_calls_evicted"] += 1
        else:
            call = calls.pop(key, None)
            if call is None:
                tied_results[key] = (when, event, prior)
            if "selection_reasons" in event:
                if call is not None:
                    event["call"] = call
                else:
                    event["pairing"] = "call_not_found_in_bounded_scan"
    for index, relative in archive["selected"].keys() - archive_seen:
        gap("archive_selected_rollout_not_reached_in_bounded_scan", index, relative)
    if counts["pending_calls_evicted"]:
        truncated.add("max_pending_calls")
    counts["sessions_included"] = len(sessions)
    for sid, session in sessions.items():
        session["source_files"] = source_files[sid]
        session["events"].sort(key=lambda event: event["timestamp"])
    bundle = {"schema": "codex-evidence-index.v3", "source_host": _label(source_host),
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "window": {"after": checkpoint.isoformat() if checkpoint else None, "through": upper_bound.isoformat() if upper_bound else None},
            "roots": [str(root.resolve()) for root in source_roots], "limits": limits,
            "coverage": counts, "source_gaps": gaps, "truncation": sorted(truncated),
            "archive_metadata": {"status": archive["status"], "rows_read": archive["rows_read"],
                                 "selected_rollouts": len(archive["selected"])},
            "complete_within_supported_scope": not gaps and not truncated,
            "limitations": ["bounded rescan; no persistent incremental offsets or checkpoint acknowledgment",
                            ("archive metadata database not integrated; window selects record activity only" if not archive_db else
                             "archive state is a current snapshot, not full archive/unarchive history; stale snapshot freshness cannot be proven"),
                            "signals are candidates; authority and outcome require contextual review",
                            "unsupported record kinds are counted, not interpreted"],
            "sessions": sorted(sessions.values(), key=lambda session: session["id"] or "")}

    return _bound_index(bundle)


def _bound_index(bundle):
    """Retain a prefix of whole events that fits the intake artifact ceiling.

    Trimming never establishes completeness. References and pairing stay intact,
    while emitted counters describe only retained events, not discarded evidence.
    """
    def fits():
        size = 1  # final newline written by _write_private
        for chunk in json.JSONEncoder(indent=2).iterencode(bundle):
            size += len(chunk.encode("utf-8"))
            if size > MAX_INDEX_BYTES:
                return False
        return True

    if fits():
        return bundle
    bundle["complete_within_supported_scope"] = False
    bundle["truncation"] = sorted(set(bundle["truncation"]) | {"max_output_bytes"})
    sessions = bundle["sessions"]
    gaps = bundle["source_gaps"]

    def retain_events(count):
        kept = []
        for session in sessions:
            events = session["events"][:count]
            if events:
                kept.append({**session, "events": events})
                count -= len(events)
            if not count:
                break
        bundle["sessions"] = kept
        bundle["coverage"]["sessions_included"] = len(kept)
        bundle["coverage"]["emitted_events"] = sum(len(s["events"]) for s in kept)

    def largest_prefix(total, retain):
        low, high = 0, total
        while low < high:
            middle = (low + high + 1) // 2
            retain(middle)
            if fits():
                low = middle
            else:
                high = middle - 1
        retain(low)

    total = bundle["coverage"]["emitted_events"]
    retain_events(0)
    if not fits():
        # Even diagnostic paths can fill the artifact; the truncation marker
        # explicitly covers omitted gaps as well as omitted events.
        bundle["source_gaps"] = []
        if not fits():
            raise ValueError("Index roots and fixed metadata exceed output ceiling")
        largest_prefix(len(gaps), lambda n: bundle.update(source_gaps=gaps[:n]))
    largest_prefix(total, retain_events)
    return bundle


def detail(source_roots: list[Path], ref: dict[str, Any], *, max_bytes: int = MAX_RECORD_BYTES,
           max_chars: int = 4000) -> dict[str, Any]:
    """Read exactly one hash-bound reference under an approved root, without scanning."""
    if not isinstance(ref, dict):
        raise ValueError("Source reference must be an object")
    if not 1 <= max_bytes <= MAX_RECORD_BYTES or not 1 <= max_chars <= 16000:
        raise ValueError("Detail limits exceed allowed bounds")
    index, offset, length = (ref.get(key) for key in ("root_index", "byte_offset", "byte_length"))
    if any(not isinstance(value, int) or isinstance(value, bool) for value in (index, offset, length)):
        raise ValueError("Invalid source reference")
    if not 0 <= index < len(source_roots) or offset < 0 or not 0 < length <= max_bytes:
        raise ValueError("Source reference exceeds bounds")
    relative = ref.get("relative_path")
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Source reference must be relative to an approved root")
    root = source_roots[index].resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root) or path.suffix != ".jsonl":
        raise ValueError("Source reference outside approved roots")
    if any(part.is_symlink() for part in [path, *list(path.parents)[:len(Path(relative).parts) - 1]]):
        raise ValueError("Symlink source references are not supported")
    with _open_source(root, relative) as handle:
        if offset:
            handle.seek(offset - 1)
            if handle.read(1) != b"\n":
                raise ValueError("Reference does not start at a record boundary")
        handle.seek(offset)
        raw = handle.read(length)
        at_eof = os.fstat(handle.fileno()).st_size == offset + length
    complete_boundary = ((raw.endswith(b"\n") and raw.count(b"\n") == 1)
                         or (at_eof and b"\n" not in raw))
    if len(raw) != length or not complete_boundary or _hash(raw) != ref.get("sha256"):
        raise ValueError("Source changed or reference is not one complete record")
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError("Detail record must be an object")
    item = record.get("payload", record)
    if not isinstance(item, dict):
        raise ValueError("Unsupported detail record")
    kind = item.get("type")
    text = _tool_text(item) if kind in tuple(RESULTS) else _text(item)
    if kind in tuple(CALLS):
        value = item.get("arguments", item.get("input", ""))
        text = value if isinstance(value, str) else json.dumps(value)
    text = EMAIL.sub("[EMAIL]", URL.sub("[URL]", SECRET.sub("[REDACTED]", PRIVATE_KEY.sub("[PRIVATE KEY]", text))))
    return {"source_ref": ref, "privacy": "private opt-in excerpt; heuristic redaction is not publication clearance",
            "text": text[:max_chars], "truncated": len(text) > max_chars}


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _boundary(value: str) -> dt.datetime:
    parsed = _time(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("requires an ISO timestamp with timezone")
    return parsed


def _write_private(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Output and its directory must not be symlinks")
    parent = path.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o077:
        raise ValueError("Output directory must be owned by this user with mode 0700")
    fd, temporary = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", action="append", type=Path, required=True)
    parser.add_argument("--source-host", required=True)
    parser.add_argument("--checkpoint", type=_boundary)
    parser.add_argument("--upper-bound", type=_boundary)
    parser.add_argument("--exclude-session", action="append", default=[])
    parser.add_argument("--archive-db", type=Path, help="optional approved standalone Codex state snapshot (WAL unsupported)")
    parser.add_argument("--archive-db-root", action="append", type=Path, default=[], help="approved database directory")
    for name, default in (("max-files", 1000), ("max-scan-records", 100000), ("max-bytes", 64 * 1024 * 1024),
                          ("max-line-bytes", MAX_RECORD_BYTES), ("max-events", 5000), ("max-sessions", 500),
                          ("max-pending-calls", 5000), ("max-directory-entries", 10000),
                          ("max-archive-bytes", 64 * 1024 * 1024), ("max-archive-rows", 10000),
                          ("max-archive-query-steps", 1000000)):
        parser.add_argument("--" + name, type=_positive, default=default)
    parser.add_argument("--detail-ref", type=Path, help="private JSON source_ref object; read only this record")
    parser.add_argument("--detail-max-chars", type=_positive, default=4000)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", type=Path, required=True, help="private output; parent must have mode 0700")
    args = parser.parse_args()
    if not args.authorized:
        parser.error("history access requires explicit --authorized invocation")
    if not args.detail_ref and (not args.exclude_session or any(not sid.strip() for sid in args.exclude_session)):
        parser.error("scan requires a nonempty --exclude-session for the current session")
    try:
        if args.detail_ref:
            reference_path = args.detail_ref.absolute()
            anchor = Path(reference_path.anchor)
            with _open_source(anchor, str(reference_path.relative_to(anchor))) as handle:
                raw_ref = handle.read(16385)
            if len(raw_ref) > 16384:
                raise ValueError("Detail reference exceeds bounds")
            result = detail(args.source_root, json.loads(raw_ref), max_chars=args.detail_max_chars)
        else:
            names = ("max_files", "max_scan_records", "max_bytes", "max_line_bytes", "max_events", "max_sessions", "max_pending_calls", "max_directory_entries")
            result = collect(args.source_root, args.checkpoint, args.upper_bound, set(args.exclude_session),
                             archive_db=args.archive_db, archive_db_roots=args.archive_db_root,
                             max_archive_bytes=args.max_archive_bytes, max_archive_rows=args.max_archive_rows,
                             max_archive_query_steps=args.max_archive_query_steps,
                             source_host=args.source_host, **{name: getattr(args, name) for name in names})
        _write_private(args.output, result)
    except (ValueError, OSError, TypeError, RecursionError):
        parser.exit(2, "Collector failed: invalid arguments, unsafe output, changed detail source, or inaccessible path.\n")


if __name__ == "__main__":
    main()
