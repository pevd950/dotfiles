"""Private local intake. No transport, review verdicts, or all-source checkpoints."""
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

MAX_INPUT = 8 * 1024 * 1024
MAX_LEDGER = 32 * 1024 * 1024
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def label(value):
    if not isinstance(value, str) or not LABEL.fullmatch(value):
        raise ValueError("Invalid identifier")
    return value


def stamp(value):
    if not isinstance(value, str):
        raise ValueError("Explicit timestamp required")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("Timestamp needs timezone")
        return result.astimezone(dt.timezone.utc).isoformat()
    except (ValueError, OverflowError) as error:
        raise ValueError("Invalid timezone-aware timestamp") from error


def window(value):
    after, through = stamp(value["after"]), stamp(value["through"])
    if after >= through:
        raise ValueError("Empty or reversed window")
    return {"after": after, "through": through}


@contextmanager
def directory(path):
    """Walk absolute paths using pinned descriptors; reject every symlink."""
    path = Path(path).absolute()
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            if part in (".", ".."):
                raise ValueError("Unsafe path")
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("Directory must be owned and mode 0700")
        yield fd
    finally:
        os.close(fd)


def read_at(fd, name, limit):
    source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        before = os.fstat(source)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or stat.S_IMODE(before.st_mode) != 0o600 or before.st_nlink != 1
                or before.st_size > limit):
            raise ValueError("Unsafe or oversized artifact")
        chunks, size = [], 0
        while size <= limit:
            chunk = os.read(source, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        after = os.fstat(source)
        if size > limit or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("Artifact changed or exceeds limit")
        return b"".join(chunks)
    finally:
        os.close(source)


def read_private(path, limit=MAX_INPUT):
    path = Path(path)
    with directory(path.parent) as fd:
        return read_at(fd, path.name, limit)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def reference(ref, roots):
    if not isinstance(ref, dict):
        raise ValueError("Invalid source reference")
    fields(ref, "root_index relative_path byte_offset byte_length sha256")
    path = ref.get("relative_path")
    if not isinstance(path, str) or not path or path.startswith("/") or any(p in ("", ".", "..") for p in path.split("/")):
        raise ValueError("Unsafe source reference")
    for name in ("root_index", "byte_offset", "byte_length"):
        if type(ref.get(name)) is not int or ref[name] < (1 if name == "byte_length" else 0):
            raise ValueError("Invalid source position")
    if ref["root_index"] >= roots or not isinstance(ref.get("sha256"), str) or not HEX.fullmatch(ref["sha256"]):
        raise ValueError("Invalid source digest or root")


def fields(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed.split()):
        raise ValueError("Unknown metadata fields")


def strings(value):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("Expected metadata strings")


def metadata_label(value):
    if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value)):
        raise ValueError("Invalid metadata label")


def source_file(value, roots):
    fields(value, "root_index relative_path")
    # Reuse the same bounded-root and relative-path contract as detail references.
    reference({**value, "byte_offset": 0, "byte_length": 1, "sha256": "0" * 64}, roots)


def validate(bundle, host, expected):
    if not isinstance(bundle, dict) or bundle.get("schema") != "codex-evidence-index.v2" or bundle.get("source_host") != host:
        raise ValueError("Wrong collector schema or host")
    fields(bundle, "schema source_host generated_at window roots limits coverage source_gaps truncation archive_metadata complete_within_supported_scope limitations sessions")
    fields(bundle["window"], "after through")
    stamp(bundle["generated_at"])
    if window(bundle["window"]) != expected:
        raise ValueError("Collector window mismatch")
    for key in ("sessions", "roots", "source_gaps", "truncation", "limitations"):
        if not isinstance(bundle.get(key), list):
            raise ValueError("Missing collector collection")
    if not bundle["roots"] or not all(isinstance(r, str) and r for r in bundle["roots"]):
        raise ValueError("Invalid roots")
    strings(bundle["limitations"])
    strings(bundle["truncation"])
    fields(bundle["limits"], "max_files max_scan_records max_bytes max_line_bytes max_events max_sessions max_pending_calls max_directory_entries max_archive_bytes max_archive_rows max_archive_query_steps")
    if not bundle["limits"] or any(type(v) is not int or v <= 0 for v in bundle["limits"].values()):
        raise ValueError("Invalid collector limits")
    archive = bundle["archive_metadata"]
    fields(archive, "status rows_read selected_rollouts")
    if archive.get("status") not in ("disabled", "unavailable", "snapshot_read") or any(type(archive.get(k)) is not int or archive[k] < 0 for k in ("rows_read", "selected_rollouts")):
        raise ValueError("Invalid archive metadata")
    for gap in bundle["source_gaps"]:
        fields(gap, "reason root_index relative_path")
        if not isinstance(gap.get("reason"), str):
            raise ValueError("Invalid source gap")
        if gap.get("relative_path") is not None and not isinstance(gap["relative_path"], str):
            raise ValueError("Invalid source gap path")
        if "root_index" in gap:
            source_file({"root_index": gap["root_index"], "relative_path": gap.get("relative_path") or "root"}, len(bundle["roots"]))
    coverage = bundle.get("coverage")
    if not isinstance(coverage, dict) or not coverage or any(type(v) is not int or v < 0 for v in coverage.values()):
        raise ValueError("Invalid coverage")
    required = set("files_discovered files_read directory_entries bytes_read records_read malformed_records incomplete_trailing_records duplicate_records untimestamped_events out_of_window_events excluded_session_files excluded_sidecar_files unsupported_records emitted_events pending_calls_evicted sessions_included".split())
    if set(coverage) != required:
        raise ValueError("Unsupported coverage counters")
    if type(bundle.get("complete_within_supported_scope")) is not bool:
        raise ValueError("Invalid completeness")
    seen = set()
    total = 0
    for session in bundle["sessions"]:
        fields(session, "id source_class events archived_at source_files")
        sid = session["id"]
        if not isinstance(sid, str) or not sid or sid in seen or not isinstance(session["events"], list):
            raise ValueError("Invalid session")
        seen.add(sid)
        if session.get("source_class") not in ("primary", "subagent", "unknown", "approval_sidecar"):
            raise ValueError("Invalid source class")
        if not isinstance(session.get("source_files"), list):
            raise ValueError("Invalid session provenance")
        for source in session["source_files"]:
            source_file(source, len(bundle["roots"]))
        if "archived_at" in session and type(session["archived_at"]) is not int:
            raise ValueError("Invalid archive timestamp")
        for event in session["events"]:
            total += 1
            fields(event, "kind name status signals timestamp source_ref mirror_source_refs correlation_id pairing selection_reasons call")
            if event.get("kind") not in ("tool_call", "tool_result", "user_message", "assistant_message"):
                raise ValueError("Invalid event")
            if "name" in event:
                metadata_label(event["name"])
            for key in ("signals", "mirror_source_refs"):
                if key in event and not isinstance(event[key], list):
                    raise ValueError("Invalid event metadata collection")
            if "signals" in event:
                strings(event["signals"])
            for key in ("correlation_id", "pairing"):
                if key in event and not isinstance(event[key], str):
                    raise ValueError("Invalid event metadata scalar")
            when = stamp(event["timestamp"])
            if when > expected["through"]:
                raise ValueError("Future event")
            if "status" in event:
                fields(event["status"], "exit_code exit_code_source is_error")
                for key, kind in (("exit_code", int), ("exit_code_source", str), ("is_error", bool)):
                    if key in event["status"] and type(event["status"][key]) is not kind:
                        raise ValueError("Invalid result status")
            reasons = event.get("selection_reasons")
            if not isinstance(reasons, list) or not reasons or not set(reasons) <= {"record_activity_in_window", "session_archived_in_window"}:
                raise ValueError("Invalid selection")
            if "record_activity_in_window" in reasons and not expected["after"] < when <= expected["through"]:
                raise ValueError("Event outside window")
            if "session_archived_in_window" in reasons:
                archived_at = session.get("archived_at")
                if type(archived_at) is not int or not 0 < archived_at <= 253402300799:
                    raise ValueError("Invalid archive timestamp")
                archived_when = dt.datetime.fromtimestamp(archived_at, dt.timezone.utc).isoformat()
                if not expected["after"] < archived_when <= expected["through"]:
                    raise ValueError("Archive selection outside window")
            reference(event["source_ref"], len(bundle["roots"]))
            for ref in event.get("mirror_source_refs", []):
                reference(ref, len(bundle["roots"]))
            if "call" in event:
                fields(event["call"], "name timestamp source_ref before_window")
                metadata_label(event["call"].get("name"))
                stamp(event["call"]["timestamp"])
                if type(event["call"].get("before_window")) is not bool:
                    raise ValueError("Invalid call window marker")
                reference(event["call"]["source_ref"], len(bundle["roots"]))
    if coverage["sessions_included"] != len(seen) or coverage["emitted_events"] != total:
        raise ValueError("Coverage counts disagree with input")
    errors = any(coverage.get(k, 0) for k in ("malformed_records", "incomplete_trailing_records", "pending_calls_evicted"))
    return bundle["complete_within_supported_scope"] and not bundle["source_gaps"] and not bundle["truncation"] and not errors


def persist(fd, ledger):
    raw = encode(ledger)
    if len(raw) > MAX_LEDGER:
        raise ValueError("Ledger capacity reached; no change written")
    temp = ".pending-" + uuid.uuid4().hex
    out = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        with os.fdopen(out, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, "ledger.json", src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        try:
            os.unlink(temp, dir_fd=fd)
        except FileNotFoundError:
            pass


@contextmanager
def locked(path):
    with directory(path) as fd:
        lock = os.open("lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
        try:
            info = os.fstat(lock)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
                raise ValueError("Unsafe lock")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                ledger = decode(read_at(fd, "ledger.json", MAX_LEDGER))
            except FileNotFoundError:
                ledger = {"schema": "central-intake.v1", "runs": {}, "acknowledged_collector_windows": {}}
            if ledger.get("schema") != "central-intake.v1":
                raise ValueError("Unsupported ledger")
            yield fd, ledger
        finally:
            os.close(lock)


def intake(state, run_id, hosts):
    """hosts maps labels to explicit status, window and (for available) bundle path."""
    label(run_id)
    if not isinstance(hosts, dict) or not 1 <= len(hosts) <= 32:
        raise ValueError("Supply 1..32 explicit hosts")
    with locked(state) as (fd, ledger):
        result = {"hosts": {}, "events": {}, "all_sources_complete": False,
                  "unsupported": ["full archive history and freshness", "memory", "inventory", "automation", "repository context"]}
        for host, spec in sorted(hosts.items()):
            label(host)
            expected = window(spec["window"])
            status = spec["status"]
            if status not in ("available", "offline", "unavailable"):
                raise ValueError("Unsupported host status")
            entry = {"window": expected, "status": status, "eligible": False}
            result["hosts"][host] = entry
            if status != "available":
                continue
            try:
                raw = read_private(spec["path"])
                entry["input_sha256"] = hashlib.sha256(raw).hexdigest()
                bundle = decode(raw)
                eligible = validate(bundle, host, expected)
            except (OSError, ValueError, KeyError, TypeError, RecursionError):
                entry["status"] = "invalid_or_denied"
                continue
            entry.update(bundle=bundle, eligible=eligible, status="complete_supported" if eligible else "partial")
            for session in bundle["sessions"]:
                occurrences = {}
                for event in session["events"]:
                    sha = event["source_ref"]["sha256"]
                    occurrences[sha] = occurrences.get(sha, 0) + 1
                    identity = digest([session["id"], sha, occurrences[sha]])
                    record = result["events"].setdefault(identity, {"session": session["id"], "raw_sha256": sha, "occurrence": occurrences[sha], "provenance": []})
                    record["provenance"].append({"host": host, "source_ref": event["source_ref"], "bundle_sha256": entry["input_sha256"]})
        result["digest"] = digest(result)
        previous = ledger["runs"].get(run_id)
        if previous is not None:
            if previous != result:
                raise ValueError("Run identity already binds different input; use a new run")
            return result
        ledger["runs"][run_id] = result
        persist(fd, ledger)
        return result


def acknowledge(state, run_id, run_digest, host, previous):
    """Explicit compare-and-swap of one supported collector window only."""
    with locked(state) as (fd, ledger):
        run = ledger["runs"][run_id]
        entry = run["hosts"][host]
        prior = stamp(previous)
        current = ledger["acknowledged_collector_windows"].get(host)
        if run["digest"] != run_digest or not entry["eligible"] or entry["window"]["after"] != prior:
            raise ValueError("Acknowledgment requires complete input and matching window")
        target = {"through": entry["window"]["through"], "run": run_id, "digest": run_digest}
        if current == target:
            return
        if current is not None and current["through"] != prior:
            raise ValueError("Previous checkpoint mismatch")
        ledger["acknowledged_collector_windows"][host] = target
        persist(fd, ledger)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--authorized", action="store_true", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("intake")
    scan.add_argument("--run", required=True)
    scan.add_argument("--manifest", required=True, type=Path)
    ack = sub.add_parser("acknowledge")
    for name in ("run", "digest", "host", "previous"):
        ack.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        if args.command == "intake":
            intake(args.state, args.run, decode(read_private(args.manifest)))
        else:
            acknowledge(args.state, args.run, args.digest, args.host, args.previous)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        parser.exit(1, "Intake failed; inspect private inputs and ledger.\n")


if __name__ == "__main__":
    main()
