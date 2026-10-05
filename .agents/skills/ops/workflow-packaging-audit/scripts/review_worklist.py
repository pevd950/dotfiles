#!/usr/bin/env python3
"""Build and checkpoint a deduplicated, no-change-capable chat review queue."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from read_transcripts import connect, refresh_inventory, stamp, verify_index_bytes
from transcript_cache import cache_path, locked_cache, private_dir, read_json, write_json

LEDGER = 'review-ledger.json'
KINDS = ('user_message', 'assistant_message', 'tool_call', 'tool_result')
DISPOSITIONS = ('no_change', 'finding', 'needs_more_evidence')


def origin(root, relative):
    """Read only the file header; guardian/fork sessions are not user chats."""
    with cache_path(root, relative).open('rb') as handle:
        raw = handle.readline(2 * 1024 * 1024)
    try:
        record = json.loads(raw)
        source = record.get('payload', {}).get('source')
        if isinstance(source, dict) and isinstance(source.get('subagent'), dict):
            return 'guardian' if source['subagent'].get('other') == 'guardian' else 'subagent'
        return 'main'
    except (ValueError, TypeError, AttributeError):
        return 'unknown'


def build(root, snapshot, connection, after, through):
    low, high = stamp(after), stamp(through)
    if low >= high:
        raise ValueError('Empty or reversed window')
    refresh_inventory(connection, snapshot)
    rows = connection.execute("""SELECT f.path,f.source,f.area,f.owner,r.line,r.stamp,r.kind,r.session,r.sha256,r.summary
      FROM records r JOIN files f ON f.id=r.file
      WHERE f.listed=1 AND f.status='complete' AND r.excluded=0
      AND r.kind IN ('user_message','assistant_message','tool_call','tool_result')
      AND ((r.stamp>? AND r.stamp<=?) OR r.stamp IS NULL)
      ORDER BY f.source,f.path,r.line""", (low, high))
    files = {}
    groups = {}
    for row in rows:
        path = row['path']
        if path not in files:
            files[path] = origin(root, path)
        provenance = files[path]
        # Session identities, not filenames or repeated copied rows, own work.
        identity = row['session'] or row['owner'] or path
        key = json.dumps([row['source'], identity, provenance], separators=(',', ':'))
        group = groups.setdefault(key, {'key': key, 'source': row['source'],
            'source_host': snapshot['sources'][row['source']].get('identity', {}).get('hostname'),
            'session_id': identity, 'origin': provenance, 'files': set(), 'events': set(),
            'signals': set(), 'user_turns': set(), 'activity_times': [], 'undated': 0,
            'anchor': None, 'archive_appearance': None})
        group['files'].add(path)
        group['events'].add(row['sha256'])
        if row['stamp']:
            group['activity_times'].append(row['stamp'])
        else:
            group['undated'] += 1
        if row['kind'] == 'user_message':
            group['user_turns'].add(row['sha256'])
        if group['anchor'] is None or (row['kind'] == 'user_message' and group['anchor_kind'] != 'user_message'):
            group['anchor'] = {'path': path, 'line': row['line']}
            group['anchor_kind'] = row['kind']
        try:
            group['signals'].update(json.loads(row['summary']).get('signals', []))
        except (ValueError, TypeError, AttributeError):
            pass
    # A newly observed archive may have no activity timestamp in the window.
    # Its observation is an interval, not a claimed exact archive time.
    for label, source in snapshot['sources'].items():
        for path, item in source.get('files', {}).items():
            observed = item.get('archive_observed_after')
            if item.get('area') != 'archived_sessions' or not observed:
                continue
            try:
                if not low < stamp(observed) <= high:
                    continue
            except ValueError:
                continue
            file = connection.execute("SELECT * FROM files WHERE path=? AND listed=1 AND status='complete'", (path,)).fetchone()
            if file is None:
                continue
            provenance = files.setdefault(path, origin(root, path))
            identity = file['owner'] or path
            key = json.dumps([label, identity, provenance], separators=(',', ':'))
            group = groups.setdefault(key, {'key': key, 'source': label,
                'source_host': source.get('identity', {}).get('hostname'),
                'session_id': identity, 'origin': provenance, 'files': set(), 'events': set(),
                'signals': set(), 'user_turns': set(), 'activity_times': [], 'undated': 0,
                'anchor': None, 'archive_appearance': None})
            anchor = connection.execute("SELECT line FROM records WHERE file=? AND excluded=0 AND kind='user_message' ORDER BY line LIMIT 1", (file['id'],)).fetchone()
            group['files'].add(path)
            group['events'].add(item['sha256'])
            group['archive_appearance'] = observed
            if group['anchor'] is None and anchor:
                group['anchor'] = {'path': path, 'line': anchor['line']}
    output = []
    for group in groups.values():
        digest = hashlib.sha256()
        for event in sorted(group.pop('events')):
            digest.update(event.encode('ascii'))
        group['fingerprint'] = digest.hexdigest()
        times = group.pop('activity_times')
        group['first_activity'] = min(times) if times else None
        group['last_activity'] = max(times) if times else None
        group['file_count'] = len(group.pop('files'))
        group['user_turn_count'] = len(group.pop('user_turns'))
        group['signals'] = sorted(group['signals'])
        group.pop('anchor_kind', None)
        output.append(group)
    output.sort(key=lambda g: (g['origin'] != 'main', not g['signals'],
                               g['last_activity'] or '', g['source'], g['session_id']), reverse=False)
    return output


def worklist(cache, after, through):
    with locked_cache(cache) as root:
        snapshot = read_json(root / 'snapshot.json')
        ledger_path = root / LEDGER
        ledger = read_json(ledger_path) if ledger_path.exists() else {'items': {}}
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, snapshot)
                verify_index_bytes(connection, root)
                groups = build(root, snapshot, connection, after, through)
        finally:
            connection.close()
        for group in groups:
            reviewed = ledger['items'].get(group['key'], {})
            group['disposition'] = reviewed.get('disposition') if reviewed.get('fingerprint') == group['fingerprint'] else None
        primary = [g for g in groups if g['origin'] in ('main','unknown') and
                   (g['user_turn_count'] or g['archive_appearance'])]
        supporting = [g for g in groups if g not in primary and g['origin'] != 'guardian']
        return {'window': {'after': stamp(after), 'through': stamp(through)},
                'primary_total': len(primary),
                'primary_pending': sum(g['disposition'] is None for g in primary),
                'primary_with_undated_activity': sum(bool(g['undated']) for g in primary),
                'primary_with_archive_appearance': sum(bool(g['archive_appearance']) for g in primary),
                'supporting_total': len(supporting),
                'supporting_pending': sum(g['disposition'] is None for g in supporting),
                'guardian_groups_excluded': sum(g['origin'] == 'guardian' for g in groups),
                'primary': primary, 'supporting': supporting,
                'interpretation': 'A worklist is not model review. Only exact-fingerprint dispositions count; supporting groups and source gaps remain explicit.'}


def mark(cache, after, through, input_path):
    changes = read_json(input_path)
    if not isinstance(changes, list) or not changes:
        raise ValueError('Expected nonempty review decisions')
    with locked_cache(cache) as root:
        snapshot = read_json(root / 'snapshot.json')
        ledger_path = root / LEDGER
        ledger = read_json(ledger_path) if ledger_path.exists() else {'items': {}}
        connection = connect(root)
        try:
            with connection:
                refresh_inventory(connection, snapshot)
                verify_index_bytes(connection, root)
                current = {g['key']: g for g in build(root, snapshot, connection, after, through)}
        finally:
            connection.close()
        if len({item.get('key') for item in changes}) != len(changes):
            raise ValueError('Duplicate review decision')
        for item in changes:
            group = current.get(item.get('key'))
            if (group is None or group['fingerprint'] != item.get('fingerprint') or
                    item.get('disposition') not in DISPOSITIONS):
                raise ValueError('Stale or invalid review decision')
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        for item in changes:
            ledger['items'][item['key']] = {'fingerprint': item['fingerprint'],
                'disposition': item['disposition'], 'reviewed_at': now}
        write_json(ledger_path, ledger)
        return {'marked': len(changes), 'reviewed_at': now}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--authorized', action='store_true', required=True)
    command = parser.add_subparsers(dest='command', required=True)
    for name in ('list','mark'):
        p = command.add_parser(name)
        p.add_argument('--after', required=True)
        p.add_argument('--through', required=True)
        if name == 'list':
            p.add_argument('--output', type=Path, required=True)
        else:
            p.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == 'list':
            result = worklist(args.cache, args.after, args.through)
            private_dir(args.output.parent)
            write_json(args.output, result)
            print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)}, indent=2))
        else:
            print(json.dumps(mark(args.cache, args.after, args.through, args.input), indent=2))
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        parser.exit(1, 'Review worklist failed; inspect private cache and decisions.\n')


if __name__ == '__main__':
    main()
