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

from scan_codex_sessions import MAX_RECORD_BYTES, SECRET, SIGNAL_PATTERNS

MAX_INPUT = 8 * 1024 * 1024
MAX_LEDGER = 32 * 1024 * 1024
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
OPAQUE = re.compile(r"opaque:[a-f0-9]{20}\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")
# Closed vocabulary of the paired collector v2 contract, not arbitrary narratives.
LIMITATIONS = {
    "bounded rescan; no persistent incremental offsets or checkpoint acknowledgment",
    "archive metadata database not integrated; window selects record activity only",
    "archive state is a current snapshot, not full archive/unarchive history; stale snapshot freshness cannot be proven",
    "signals are candidates; authority and outcome require contextual review",
    "unsupported record kinds are counted, not interpreted",
}
TRUNCATIONS = set("max_directory_entries remaining_roots max_files max_bytes max_scan_records max_sessions max_events max_pending_calls".split())
GAPS = set("""directory_depth_limit directory_unreadable symlink_skipped entry_unreadable
root_missing_or_not_directory path_outside_root oversized_record_file_stopped
incomplete_trailing_record malformed_record invalid_session_metadata session_identity_changed
unknown_session_source missing_session_metadata record_decode_failed event_timestamp_missing_or_invalid
file_unreadable archive_selected_rollout_not_reached_in_bounded_scan archive_database_rollout_identity_mismatch
archive_database_outside_allowed_roots archive_database_requires_quiescent_snapshot archive_database_byte_limit
archive_database_changed_during_snapshot archive_database_unsupported_schema archive_database_row_limit
archive_database_invalid_or_duplicate_identity archive_database_invalid_archived_flag
archive_database_unarchived_timestamp_inconsistent archive_database_missing_or_invalid_archive_time
archive_database_archive_time_after_window archive_database_invalid_rollout_path
archive_database_rollout_outside_allowed_roots archive_database_rollout_missing_or_unsafe
archive_snapshot_freshness_unverified archive_database_unreadable_invalid_or_query_limit""".split())


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
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError("Invalid metadata label")
    if OPAQUE.fullmatch(value):
        return
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value) or SECRET.search(value):
        raise ValueError("Invalid or unscreened metadata label")


def source_file(value, roots, require_jsonl=False):
    fields(value, "root_index relative_path")
    # Reuse the same bounded-root and relative-path contract as detail references.
    reference({**value, "byte_offset": 0, "byte_length": 1, "sha256": "0" * 64}, roots)
    if require_jsonl and Path(value["relative_path"]).suffix != ".jsonl":
        raise ValueError("Source file must be JSONL")


def validate(bundle, host, expected):
    if not isinstance(bundle, dict) or bundle.get("schema") != "codex-evidence-index.v2" or bundle.get("source_host") != host:
        raise ValueError("Wrong collector schema or host")
    metadata_label(bundle.get("source_host"))
    fields(bundle, "schema source_host generated_at window roots limits coverage source_gaps truncation archive_metadata complete_within_supported_scope limitations sessions")
    fields(bundle["window"], "after through")
    generated_at = stamp(bundle["generated_at"])
    if window(bundle["window"]) != expected:
        raise ValueError("Collector window mismatch")
    for key in ("sessions", "roots", "source_gaps", "truncation", "limitations"):
        if not isinstance(bundle.get(key), list):
            raise ValueError("Missing collector collection")
    if not bundle["roots"] or not all(isinstance(r, str) and r for r in bundle["roots"]):
        raise ValueError("Invalid roots")
    strings(bundle["limitations"])
    strings(bundle["truncation"])
    if not set(bundle["limitations"]) <= LIMITATIONS or not set(bundle["truncation"]) <= TRUNCATIONS:
        raise ValueError("Unknown collector narrative")
    limits = set("max_files max_scan_records max_bytes max_line_bytes max_events max_sessions max_pending_calls max_directory_entries max_archive_bytes max_archive_rows max_archive_query_steps".split())
    if not isinstance(bundle["limits"], dict) or set(bundle["limits"]) != limits or any(type(v) is not int or v <= 0 for v in bundle["limits"].values()):
        raise ValueError("Invalid collector limits")
    if bundle["limits"]["max_line_bytes"] > MAX_RECORD_BYTES:
        raise ValueError("Record limit exceeds detail retrieval ceiling")
    archive = bundle["archive_metadata"]
    fields(archive, "status rows_read selected_rollouts")
    if archive.get("status") not in ("disabled", "unavailable", "snapshot_read") or any(type(archive.get(k)) is not int or archive[k] < 0 for k in ("rows_read", "selected_rollouts")):
        raise ValueError("Invalid archive metadata")
    if archive["status"] == "disabled" and (archive["rows_read"] or archive["selected_rollouts"]):
        raise ValueError("Disabled archive has activity")
    for gap in bundle["source_gaps"]:
        fields(gap, "reason root_index relative_path")
        if not isinstance(gap.get("reason"), str) or gap["reason"] not in GAPS:
            raise ValueError("Invalid source gap")
        if gap.get("relative_path") is not None and not isinstance(gap["relative_path"], str):
            raise ValueError("Invalid source gap path")
        if "root_index" in gap:
            relative = gap.get("relative_path")
            source_file({"root_index": gap["root_index"], "relative_path": "root" if relative in (None, ".") else relative}, len(bundle["roots"]))
    coverage = bundle.get("coverage")
    if not isinstance(coverage, dict) or not coverage or any(type(v) is not int or v < 0 for v in coverage.values()):
        raise ValueError("Invalid coverage")
    required = set("files_discovered files_read directory_entries bytes_read records_read malformed_records incomplete_trailing_records duplicate_records untimestamped_events out_of_window_events excluded_session_files excluded_sidecar_files unsupported_records emitted_events pending_calls_evicted sessions_included".split())
    if set(coverage) != required:
        raise ValueError("Unsupported coverage counters")
    bounded = {"records_read": "max_scan_records", "bytes_read": "max_bytes",
               "files_discovered": "max_files", "files_read": "max_files",
               "directory_entries": "max_directory_entries", "sessions_included": "max_sessions",
               "emitted_events": "max_events"}
    within_limits = all(coverage[counter] <= bundle["limits"][limit] for counter, limit in bounded.items())
    if (coverage["records_read"] < coverage["emitted_events"]
            or coverage["files_read"] > coverage["files_discovered"]
            or coverage["sessions_included"] > coverage["files_read"]
            or coverage["sessions_included"] > coverage["emitted_events"]):
        raise ValueError("Inconsistent coverage counters")
    if type(bundle.get("complete_within_supported_scope")) is not bool:
        raise ValueError("Invalid completeness")
    seen = set()
    total = 0
    for session in bundle["sessions"]:
        fields(session, "id source_class events archived_at source_files")
        sid = session["id"]
        if not isinstance(sid, str) or not sid or sid in seen or not isinstance(session["events"], list):
            raise ValueError("Invalid session")
        metadata_label(sid)
        seen.add(sid)
        if session.get("source_class") not in ("primary", "subagent", "unknown"):
            raise ValueError("Invalid source class")
        if not isinstance(session.get("source_files"), list):
            raise ValueError("Invalid session provenance")
        for source in session["source_files"]:
            source_file(source, len(bundle["roots"]), require_jsonl=True)
        files = {(source["root_index"], source["relative_path"]) for source in session["source_files"]}
        def session_reference(ref):
            reference(ref, len(bundle["roots"]))
            if ref["byte_length"] > bundle["limits"]["max_line_bytes"]:
                raise ValueError("Reference exceeds collector record limit")
            if (ref["root_index"], ref["relative_path"]) not in files:
                raise ValueError("Reference outside session provenance")
        if "archived_at" in session and type(session["archived_at"]) is not int:
            raise ValueError("Invalid archive timestamp")
        if "archived_at" in session and archive["status"] != "snapshot_read":
            raise ValueError("Archive selection requires snapshot metadata")
        for event in session["events"]:
            total += 1
            fields(event, "kind name status signals timestamp source_ref mirror_source_refs correlation_id pairing selection_reasons call")
            if event.get("kind") not in ("tool_call", "tool_result", "user_message", "assistant_message"):
                raise ValueError("Invalid event")
            common = {"kind", "timestamp", "source_ref", "selection_reasons"}
            required_fields, optional = {
                "tool_call": ({"name"}, {"correlation_id"}),
                "tool_result": ({"status", "signals"}, {"correlation_id", "call", "pairing"}),
                "user_message": ({"signals"}, {"mirror_source_refs"}),
                "assistant_message": ({"signals"}, {"mirror_source_refs"}),
            }[event["kind"]]
            if not common | required_fields <= set(event) or set(event) - common - required_fields - optional:
                raise ValueError("Fields do not match event kind")
            if event["kind"] == "tool_result":
                if ("call" in event) == ("pairing" in event):
                    raise ValueError("Result needs one pairing outcome")
                needs_correlation = event.get("pairing") != "missing_call_id"
                if needs_correlation != ("correlation_id" in event):
                    raise ValueError("Result correlation does not match pairing")
            if "name" in event:
                metadata_label(event["name"])
            for key in ("signals", "mirror_source_refs"):
                if key in event and not isinstance(event[key], list):
                    raise ValueError("Invalid event metadata collection")
            if "signals" in event:
                strings(event["signals"])
                if not set(event["signals"]) <= {name for name, _ in SIGNAL_PATTERNS[event["kind"]]}:
                    raise ValueError("Signals do not match event kind")
            for key in ("correlation_id", "pairing"):
                if key in event and not isinstance(event[key], str):
                    raise ValueError("Invalid event metadata scalar")
            if "pairing" in event and event["pairing"] not in ("missing_call_id", "call_not_found_in_bounded_scan"):
                raise ValueError("Unknown pairing status")
            if "correlation_id" in event and not HEX.fullmatch(event["correlation_id"]):
                raise ValueError("Invalid correlation digest")
            when = stamp(event["timestamp"])
            if when > expected["through"]:
                raise ValueError("Future event")
            if "status" in event:
                fields(event["status"], "exit_code exit_code_source is_error")
                for key, kind in (("exit_code", int), ("exit_code_source", str), ("is_error", bool)):
                    if key in event["status"] and type(event["status"][key]) is not kind:
                        raise ValueError("Invalid result status")
                if "exit_code_source" in event["status"] and event["status"]["exit_code_source"] != "output_text_candidate":
                    raise ValueError("Unknown exit code source")
            reasons = event.get("selection_reasons")
            if not isinstance(reasons, list) or not reasons or not set(reasons) <= {"record_activity_in_window", "session_archived_in_window"}:
                raise ValueError("Invalid selection")
            if "record_activity_in_window" in reasons and not expected["after"] < when <= expected["through"]:
                raise ValueError("Event outside window")
            if "session_archived_in_window" in reasons:
                if archive["status"] != "snapshot_read":
                    raise ValueError("Archive event requires snapshot metadata")
                archived_at = session.get("archived_at")
                if type(archived_at) is not int or not 0 < archived_at <= 253402300799:
                    raise ValueError("Invalid archive timestamp")
                archived_when = dt.datetime.fromtimestamp(archived_at, dt.timezone.utc).isoformat()
                if not expected["after"] < archived_when <= expected["through"]:
                    raise ValueError("Archive selection outside window")
            session_reference(event["source_ref"])
            for ref in event.get("mirror_source_refs", []):
                session_reference(ref)
            if "call" in event:
                fields(event["call"], "name timestamp source_ref before_window")
                metadata_label(event["call"].get("name"))
                call_when = stamp(event["call"]["timestamp"])
                if type(event["call"].get("before_window")) is not bool:
                    raise ValueError("Invalid call window marker")
                if call_when > when or event["call"]["before_window"] != (call_when <= expected["after"]):
                    raise ValueError("Inconsistent paired call time")
                session_reference(event["call"]["source_ref"])
    if coverage["sessions_included"] != len(seen) or coverage["emitted_events"] != total:
        raise ValueError("Coverage counts disagree with input")
    errors = any(coverage.get(k, 0) for k in ("malformed_records", "incomplete_trailing_records",
                                              "untimestamped_events", "pending_calls_evicted"))
    # Archive snapshots cannot prove freshness even if their gap was removed.
    return (bundle["complete_within_supported_scope"] and not bundle["source_gaps"]
            and not bundle["truncation"] and not errors and archive["status"] == "disabled"
            and expected["through"] <= generated_at and within_limits
            and all(session["source_class"] in ("primary", "subagent") for session in bundle["sessions"]))


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
            if (not isinstance(ledger, dict) or ledger.get("schema") != "central-intake.v1"
                    or not isinstance(ledger.get("runs"), dict)
                    or not isinstance(ledger.get("acknowledged_collector_windows"), dict)):
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
            metadata_label(host)
            if host is None:
                raise ValueError("Host label required")
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
                    hashes = tuple(sorted({ref["sha256"] for ref in [event["source_ref"], *event.get("mirror_source_refs", [])]}))
                    occurrences[hashes] = occurrences.get(hashes, 0) + 1
                    identity = digest([session["id"], hashes, occurrences[hashes]])
                    record = result["events"].setdefault(identity, {"session": session["id"], "raw_sha256s": list(hashes), "occurrence": occurrences[hashes], "provenance": []})
                    refs = [("primary", event["source_ref"])] + [("mirror", ref) for ref in event.get("mirror_source_refs", [])]
                    for role, ref in refs:
                        record["provenance"].append({"host": host, "source_ref": ref, "role": role,
                                                     "bundle_sha256": entry["input_sha256"]})
            # Bound the live result as each host is admitted, before another
            # bundle can be retained and before the final ledger serialization.
            projected = {"schema": ledger["schema"], "runs": dict(ledger["runs"]),
                         "acknowledged_collector_windows": ledger["acknowledged_collector_windows"]}
            projected["runs"][run_id] = result
            if len(encode(projected)) > MAX_LEDGER:
                raise ValueError("Ledger capacity reached; no change written")
        result["digest"] = digest(result)
        previous = ledger["runs"].get(run_id)
        if previous is not None:
            if previous != result:
                raise ValueError("Run identity already binds different input; use a new run")
            os.fsync(fd)
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
            os.fsync(fd)
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
