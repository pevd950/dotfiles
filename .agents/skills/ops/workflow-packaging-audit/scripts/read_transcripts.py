#!/usr/bin/env python3
"""Resumable local transcript indexing and private surrounding-context reads."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from scan_codex_sessions import _event, _time
from transcript_cache import cache_path, file_hash, locked_cache, private_file, read_json, signature, write_json

SCHEMA = '''
CREATE TABLE IF NOT EXISTS files (
 id INTEGER PRIMARY KEY, path TEXT UNIQUE, source TEXT, area TEXT,
 sha256 TEXT, size INTEGER, mtime_ns INTEGER, offset INTEGER DEFAULT 0,
 line INTEGER DEFAULT 0, owner TEXT, session TEXT, status TEXT DEFAULT 'pending',
 malformed INTEGER DEFAULT 0, oversized INTEGER DEFAULT 0, untimestamped INTEGER DEFAULT 0,
 listed INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS records (
 file INTEGER, line INTEGER, offset INTEGER, length INTEGER, sha256 TEXT,
 stamp TEXT, kind TEXT, session TEXT, call_id TEXT, summary TEXT,
 PRIMARY KEY(file,line));
CREATE INDEX IF NOT EXISTS record_time ON records(stamp);
CREATE INDEX IF NOT EXISTS record_call ON records(file,call_id);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
'''


def stamp(value):
    result = _time(value)
    if result is None:
        raise ValueError('Expected a timezone-aware timestamp')
    return result.isoformat(timespec='microseconds')


def connect(root):
    path = root / 'index.sqlite3'
    if not path.exists():
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    private_file(path)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA trusted_schema=OFF')
    connection.executescript(SCHEMA)
    return connection


def refresh_inventory(connection, snapshot):
    previous = connection.execute("SELECT value FROM settings WHERE key='snapshot'").fetchone()
    if previous and previous[0] == snapshot['observed_at']:
        return
    exclusions = json.dumps(sorted(snapshot.get('exclude_sessions', [])))
    old_exclusions = connection.execute("SELECT value FROM settings WHERE key='exclusions'").fetchone()
    if old_exclusions and old_exclusions[0] != exclusions:
        connection.execute('DELETE FROM records')
        connection.execute('DELETE FROM files')
    connection.execute("INSERT OR REPLACE INTO settings VALUES('exclusions',?)", (exclusions,))
    connection.execute('UPDATE files SET listed=0')
    for source, entry in snapshot['sources'].items():
        for path, item in entry.get('files', {}).items():
            if not path.startswith(source + '/' + item['area'] + '/'):
                raise ValueError('Cache inventory/source mismatch')
            old = connection.execute('SELECT * FROM files WHERE path=?', (path,)).fetchone()
            if old and (old['sha256'] != item['sha256'] or old['status'] == 'changed'):
                connection.execute('DELETE FROM records WHERE file=?', (old['id'],))
                connection.execute("DELETE FROM files WHERE id=?", (old['id'],))
                old = None
            if old:
                connection.execute('UPDATE files SET listed=1,size=?,mtime_ns=? WHERE id=?',
                                   (item['size'], item['mtime_ns'], old['id']))
            else:
                connection.execute('INSERT INTO files(path,source,area,sha256,size,mtime_ns) VALUES(?,?,?,?,?,?)',
                                   (path, source, item['area'], item['sha256'], item['size'], item['mtime_ns']))
    connection.execute("INSERT OR REPLACE INTO settings VALUES('snapshot',?)", (snapshot['observed_at'],))


def read_record(handle, limit):
    """Read one whole record; over-limit records are drained, never hide the next."""
    raw = handle.readline(limit + 1)
    if not raw:
        return None
    digest = hashlib.sha256(raw)
    length = len(raw)
    if length <= limit:
        return raw, length, digest.hexdigest()
    while not raw.endswith(b'\n'):
        raw = handle.readline(1024 * 1024)
        if not raw:
            break
        digest.update(raw)
        length += len(raw)
    return None, length, digest.hexdigest()


def scan_batch(cache, *, max_bytes=64 * 1024 * 1024, max_records=50000,
               max_record_bytes=64 * 1024 * 1024):
    if min(max_bytes, max_records, max_record_bytes) <= 0:
        raise ValueError('Batch limits must be positive')
    with locked_cache(cache) as root:
        snapshot = read_json(root / 'snapshot.json')
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, snapshot)
                old_limit = connection.execute("SELECT value FROM settings WHERE key='record_limit'").fetchone()
                if old_limit and int(old_limit[0]) < max_record_bytes:
                    affected = connection.execute('SELECT id FROM files WHERE oversized>0').fetchall()
                    for row in affected:
                        connection.execute('DELETE FROM records WHERE file=?', (row['id'],))
                        connection.execute("UPDATE files SET offset=0,line=0,owner=NULL,session=NULL,status='pending',malformed=0,oversized=0,untimestamped=0 WHERE id=?", (row['id'],))
                connection.execute("INSERT OR REPLACE INTO settings VALUES('record_limit',?)", (str(max_record_bytes),))
                files = connection.execute("SELECT * FROM files WHERE listed=1 AND status='pending' ORDER BY source,area,path").fetchall()
                used = count = 0
                for file in files:
                    path = cache_path(root, file['path'])
                    expected = (file['size'], file['mtime_ns'])
                    offset, line = file['offset'], file['line']
                    owner, session = file['owner'], file['session']
                    malformed, oversized, untimestamped = file['malformed'], file['oversized'], file['untimestamped']
                    status = 'pending'
                    try:
                        if signature(path) != expected:
                            raise ValueError('Cache file changed')
                        with path.open('rb') as handle:
                            handle.seek(offset)
                            while used < max_bytes and count < max_records:
                                item = read_record(handle, max_record_bytes)
                                if item is None:
                                    status = 'complete'
                                    break
                                raw, length, digest = item
                                start = offset
                                offset += length
                                line += 1
                                used += length
                                count += 1
                                when = kind = call_id = None
                                summary = {}
                                if raw is None:
                                    oversized += 1
                                    kind = 'oversized_unparsed'
                                else:
                                    try:
                                        record = json.loads(raw)
                                        if not isinstance(record, dict):
                                            raise ValueError('Nonobject record')
                                        when = _time(record.get('timestamp'))
                                        if record.get('type') == 'session_meta':
                                            payload = record.get('payload', {})
                                            session = payload.get('id') if isinstance(payload, dict) else None
                                            session = session if isinstance(session, str) else None
                                            if owner is None:
                                                owner = session
                                            kind = 'session_meta'
                                        else:
                                            decoded = _event(record)
                                            if decoded:
                                                summary, call_id = decoded
                                                kind = summary['kind']
                                                if when is None:
                                                    untimestamped += 1
                                            else:
                                                kind = str(record.get('type', 'unknown'))[:160]
                                    except (ValueError, TypeError, RecursionError):
                                        malformed += 1
                                        kind = 'malformed'
                                connection.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?)',
                                    (file['id'], line, start, length, digest,
                                     when.isoformat(timespec='microseconds') if when else None,
                                     kind, session, call_id if isinstance(call_id, str) else None,
                                     json.dumps(summary)))
                                if owner in snapshot.get('exclude_sessions', []):
                                    offset = file['size']
                                    status = 'excluded'
                                    break
                            if offset == file['size']:
                                status = 'excluded' if status == 'excluded' else 'complete'
                        if signature(path) != expected:
                            raise ValueError('Cache file changed')
                        if status in ('complete', 'excluded') and file_hash(path) != file['sha256']:
                            raise ValueError('Cache digest changed')
                    except (OSError, ValueError):
                        connection.execute('DELETE FROM records WHERE file=?', (file['id'],))
                        offset = line = malformed = oversized = untimestamped = 0
                        status = 'changed'
                    connection.execute('UPDATE files SET offset=?,line=?,owner=?,session=?,status=?,malformed=?,oversized=?,untimestamped=? WHERE id=?',
                                       (offset, line, owner, session, status, malformed, oversized, untimestamped, file['id']))
                    if used >= max_bytes or count >= max_records:
                        break
            return {'batch_bytes': used, 'batch_records': count,
                    'remaining_files': connection.execute("SELECT count(*) FROM files WHERE listed=1 AND status='pending'").fetchone()[0]}
        finally:
            connection.close()


def report(cache, after, through):
    low, high = stamp(after), stamp(through)
    if low >= high:
        raise ValueError('Empty or reversed window')
    with locked_cache(cache) as root:
        snapshot = read_json(root / 'snapshot.json')
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, snapshot)
            sources = {}
            for source, entry in snapshot['sources'].items():
                rows = connection.execute('SELECT * FROM files WHERE listed=1 AND source=?', (source,)).fetchall()
                selected = connection.execute("SELECT count(*) FROM records r JOIN files f ON f.id=r.file WHERE f.listed=1 AND f.source=? AND f.status='complete' AND r.stamp>? AND r.stamp<=? AND r.kind IN ('user_message','assistant_message','tool_call','tool_result')", (source, low, high)).fetchone()[0]
                pending = sum(r['status'] == 'pending' for r in rows)
                changed = sum(r['status'] == 'changed' for r in rows)
                parse_gaps = sum(r['malformed'] + r['oversized'] + r['untimestamped'] for r in rows if r['status'] != 'excluded')
                sources[source] = {'pull_status': entry['status'], 'pull_error': entry.get('error'),
                    'last_successful_pull': entry.get('last_successful_pull'),
                    'cached_files': len(rows), 'pending_files': pending, 'changed_files': changed,
                    'excluded_files': sum(r['status'] == 'excluded' for r in rows),
                    'bytes_scanned': sum(r['offset'] for r in rows),
                    'records_scanned': sum(r['line'] for r in rows), 'selected_records': selected,
                    'malformed_records': sum(r['malformed'] for r in rows),
                    'oversized_unparsed': sum(r['oversized'] for r in rows),
                    'untimestamped_events': sum(r['untimestamped'] for r in rows),
                    'cached_traversal_complete': bool(entry.get('files') is not None) and not pending and not changed,
                    'timestamp_selection_complete': entry['status'] == 'ok' and not pending and not changed and not parse_gaps,
                    'retained_files_absent_at_source': sum(not f['present_at_source'] for f in entry.get('files', {}).values()),
                    'new_archive_observations': sum(bool(f.get('archive_observed_after')) for f in entry.get('files', {}).values())}
            return {'window': {'after': low, 'through': high}, 'sources': sources,
                    'excluded_sessions': snapshot.get('exclude_sessions', []),
                    'snapshot_observed_at': snapshot['observed_at'],
                    'all_sources_covered': all(s['timestamp_selection_complete'] for s in sources.values()),
                    'archive_history': snapshot['archive_history'],
                    'interpretation': 'Record occurrences preserve source/file attribution; copies and inherited fork history are not deduplicated. Coverage is not a completed model review.'}
        finally:
            connection.close()


def candidates(cache, after, through, *, limit=100, offset=0, kind=None, signal=None):
    if not 1 <= limit <= 1000 or offset < 0:
        raise ValueError('Invalid result page')
    with locked_cache(cache) as root:
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, read_json(root / 'snapshot.json'))
            query = "SELECT f.path,f.source,f.area,f.owner,r.* FROM records r JOIN files f ON f.id=r.file WHERE f.listed=1 AND f.status='complete' AND r.stamp>? AND r.stamp<=? AND r.kind IN ('user_message','assistant_message','tool_call','tool_result')"
            args = [stamp(after), stamp(through)]
            if kind:
                query += ' AND r.kind=?'; args.append(kind)
            if signal:
                query += ' AND r.summary LIKE ?'; args.append('%' + signal + '%')
            query += ' ORDER BY r.stamp,f.source,f.path,r.line LIMIT ? OFFSET ?'
            args.extend([limit, offset])
            rows = connection.execute(query, args).fetchall()
            return [{k: row[k] for k in ('source', 'area', 'path', 'owner', 'line', 'stamp', 'kind', 'session', 'summary')} for row in rows]
        finally:
            connection.close()


def context(cache, relative, line, *, radius=3, max_chars=4000):
    if not 0 <= radius <= 20 or not 1 <= max_chars <= 64000:
        raise ValueError('Context limits exceeded')
    with locked_cache(cache) as root:
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, read_json(root / 'snapshot.json'))
            file = connection.execute("SELECT * FROM files WHERE path=? AND listed=1 AND status='complete'", (relative,)).fetchone()
            if file is None:
                raise ValueError('File not completely indexed')
            target = connection.execute('SELECT * FROM records WHERE file=? AND line=?', (file['id'], line)).fetchone()
            if target is None:
                raise ValueError('Record not indexed')
            rows = {r['line']: r for r in connection.execute('SELECT * FROM records WHERE file=? AND line BETWEEN ? AND ?', (file['id'], line-radius, line+radius))}
            user = connection.execute("SELECT * FROM records WHERE file=? AND line<=? AND kind='user_message' ORDER BY line DESC LIMIT 1", (file['id'], line)).fetchone()
            if user:
                rows[user['line']] = user
            if target['call_id']:
                for kind, op, order in (('tool_call', '<=', 'DESC'), ('tool_result', '>=', 'ASC')):
                    related = connection.execute(f'SELECT * FROM records WHERE file=? AND call_id=? AND kind=? AND line{op}? ORDER BY line {order} LIMIT 1', (file['id'], target['call_id'], kind, line)).fetchone()
                    if related:
                        rows[related['line']] = related
            path = cache_path(root, relative)
            if signature(path) != (file['size'], file['mtime_ns']):
                raise ValueError('Cache changed; pull and reindex')
            output = []
            with private_file(path).open('rb') as handle:
                for row in sorted(rows.values(), key=lambda r: r['line']):
                    handle.seek(row['offset'])
                    remaining = row['length']; digest = hashlib.sha256(); prefix = bytearray()
                    while remaining:
                        chunk = handle.read(min(remaining, 1024*1024))
                        if not chunk:
                            raise ValueError('Cache record shortened')
                        remaining -= len(chunk); digest.update(chunk)
                        if len(prefix) < max_chars * 4:
                            prefix.extend(chunk[:max_chars*4-len(prefix)])
                    if digest.hexdigest() != row['sha256']:
                        raise ValueError('Cache record changed')
                    text = prefix.decode('utf-8', errors='replace')
                    output.append({'line': row['line'], 'timestamp': row['stamp'], 'kind': row['kind'],
                                   'record_session': row['session'], 'text': text[:max_chars],
                                   'truncated': row['length'] > len(prefix) or len(text) > max_chars})
            return {'source': file['source'], 'area': file['area'], 'path': relative,
                    'file_session': file['owner'], 'records': output,
                    'privacy': 'Private raw context, not sanitized for publication. Forked/copied records retain file and header attribution.'}
        finally:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--authorized', action='store_true', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    scan = commands.add_parser('scan')
    scan.add_argument('--until-complete', action='store_true')
    scan.add_argument('--batch-bytes', type=int, default=64*1024*1024)
    scan.add_argument('--batch-records', type=int, default=50000)
    scan.add_argument('--max-record-bytes', type=int, default=64*1024*1024)
    for name in ('report', 'candidates'):
        p = commands.add_parser(name)
        p.add_argument('--after', required=True); p.add_argument('--through', required=True)
        if name == 'candidates':
            p.add_argument('--limit', type=int, default=100); p.add_argument('--offset', type=int, default=0)
            p.add_argument('--kind'); p.add_argument('--signal'); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('context')
    p.add_argument('--path', required=True); p.add_argument('--line', type=int, required=True)
    p.add_argument('--radius', type=int, default=3); p.add_argument('--max-chars', type=int, default=4000)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); os.umask(0o077)
    try:
        if args.command == 'scan':
            while True:
                result = scan_batch(args.cache, max_bytes=args.batch_bytes, max_records=args.batch_records,
                                    max_record_bytes=args.max_record_bytes)
                print(json.dumps(result), flush=True)
                if not args.until_complete or not result['remaining_files']:
                    break
        elif args.command == 'report':
            print(json.dumps(report(args.cache, args.after, args.through), indent=2))
        else:
            result = (candidates(args.cache, args.after, args.through, limit=args.limit, offset=args.offset,
                                 kind=args.kind, signal=args.signal) if args.command == 'candidates'
                      else context(args.cache, args.path, args.line, radius=args.radius, max_chars=args.max_chars))
            from transcript_cache import private_dir
            private_dir(args.output.parent)
            write_json(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        parser.exit(1, 'Reader failed; inspect private cache state and explicit inputs.\n')


if __name__ == '__main__':
    main()
