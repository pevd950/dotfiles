"""Optional bounded read-only adapter for Codex SQLite archive state.

Only the fixed threads projection is queried; no SQL from metadata is executed.
SQLite only sees an in-memory copy. Live WAL databases fail closed because a
consistent WAL acquisition needs coordination outside this adapter's scope.
"""
import sqlite3
import os
from contextlib import closing
from pathlib import Path


def read_archive_metadata(path, allowed_roots, source_roots, lower, upper,
                          open_source, *, max_bytes, max_rows, max_query_steps):
    result = {"status": "unavailable", "rows_read": 0, "gaps": [], "selected": {}}

    def gap(reason):
        if reason not in result["gaps"]:
            result["gaps"].append(reason)

    try:
        requested = Path(path).absolute()
        roots = [variant for root in allowed_roots for variant in (Path(root).absolute(), Path(root).resolve())]
        allowed = next((root for root in roots if requested.is_relative_to(root)), None)
        if allowed is None:
            gap("archive_database_outside_allowed_roots"); return result
        root = allowed.resolve()
        requested = root / requested.relative_to(allowed)
        def sidecars_present():
            # lstat also detects dangling symlinks, without following them.
            for suffix in ("-wal", "-shm", "-journal"):
                try:
                    Path(str(requested) + suffix).lstat()
                except FileNotFoundError:
                    continue
                return True
            return False

        if sidecars_present():
            gap("archive_database_requires_quiescent_snapshot"); return result
        def signature(value):
            return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

        with open_source(root, str(requested.relative_to(root))) as handle:
            before = signature(os.fstat(handle.fileno()))
            if before[2] > max_bytes:
                gap("archive_database_byte_limit"); return result
            data = handle.read(max_bytes + 1)
            if len(data) > max_bytes:
                gap("archive_database_byte_limit"); return result
            after = signature(os.fstat(handle.fileno()))
        with open_source(root, str(requested.relative_to(root))) as handle:
            current = signature(os.fstat(handle.fileno()))
        if before != after or before != current or len(data) != before[2] or sidecars_present():
            gap("archive_database_changed_during_snapshot"); return result
        # Reject WAL-format main files even without sidecars: their checkpoint
        # completeness cannot be established from this copy alone.
        if data[18:20] != b"\x01\x01":
            gap("archive_database_requires_quiescent_snapshot"); return result
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.deserialize(data)
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("BEGIN")
            connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, min(max_bytes, 1024 * 1024))
            steps = 0

            def progress():
                nonlocal steps
                steps += 100
                return int(steps > max_query_steps)

            connection.set_progress_handler(progress, 100)
            table = connection.execute("SELECT type FROM sqlite_schema WHERE name='threads'").fetchone()
            columns = {row[1]: row[2].upper() for row in connection.execute("PRAGMA table_info(threads)")}
            if table != ("table",) or any(columns.get(key) != kind for key, kind in
                    (("id", "TEXT"), ("rollout_path", "TEXT"), ("archived", "INTEGER"), ("archived_at", "INTEGER"))):
                gap("archive_database_unsupported_schema"); return result
            def authorize(action, table, column, database, trigger):
                if action == sqlite3.SQLITE_SELECT:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and table == "threads" and column in {"id", "rollout_path", "archived", "archived_at"}:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY

            connection.set_authorizer(authorize)
            rows = connection.execute("SELECT id, rollout_path, archived, archived_at FROM threads LIMIT ?", (max_rows + 1,))
            seen = set()
            for sid, rollout, archived, archived_at in rows:
                if result["rows_read"] >= max_rows:
                    gap("archive_database_row_limit"); break
                result["rows_read"] += 1
                if not isinstance(sid, str) or not sid or len(sid) > 160 or sid in seen:
                    gap("archive_database_invalid_or_duplicate_identity"); continue
                seen.add(sid)
                if type(archived) is not int or archived not in (0, 1):
                    gap("archive_database_invalid_archived_flag"); continue
                if not archived:
                    if archived_at is not None:
                        gap("archive_database_unarchived_timestamp_inconsistent")
                    continue
                if type(archived_at) is not int or archived_at <= 0:
                    gap("archive_database_missing_or_invalid_archive_time"); continue
                if upper and archived_at > upper.timestamp():
                    gap("archive_database_archive_time_after_window"); continue
                if lower and archived_at <= lower.timestamp():
                    continue
                if not isinstance(rollout, str) or len(rollout) > 4096 or not Path(rollout).is_absolute() or ".." in Path(rollout).parts:
                    gap("archive_database_invalid_rollout_path"); continue
                target = Path(rollout)
                source = next(((index, variant) for index, root in enumerate(source_roots)
                               for variant in (root.absolute(), root.resolve())
                               if target.is_relative_to(variant)), None)
                if source is None or target.suffix != ".jsonl":
                    gap("archive_database_rollout_outside_allowed_roots"); continue
                index, source_root = source
                relative = str(target.relative_to(source_root))
                try:
                    with open_source(source_root.resolve(), relative):
                        pass
                except (OSError, ValueError):
                    gap("archive_database_rollout_missing_or_unsafe"); continue
                result["selected"][(index, relative)] = {"id": sid, "archived_at": archived_at}
        result["status"] = "snapshot_read"
        gap("archive_snapshot_freshness_unverified")
    except (OSError, ValueError, sqlite3.Error, AttributeError):
        # Never expose database values or SQLite exception text.
        result["selected"] = {}
        gap("archive_database_unreadable_invalid_or_query_limit")
    return result
