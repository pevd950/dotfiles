#!/usr/bin/env python3
"""Bound a private transcript *copy* cache without touching source transcripts."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from zoneinfo import ZoneInfo

from pull_transcripts import probe_with_retry, validate_source, RSYNC_SAFE_PATH
from read_transcripts import connect, refresh_inventory
from transcript_cache import cache_path, file_hash, locked_cache, private_file, read_json, signature, write_json


def cutoff_for_days(days, timezone, today=None):
    if days < 30:
        raise ValueError('Keep at least 30 complete local days')
    zone = ZoneInfo(timezone)
    local_day = today or dt.datetime.now(zone).date()
    return dt.datetime.combine(local_day - dt.timedelta(days=days), dt.time.min, zone).astimezone(dt.timezone.utc)


def plan(root, snapshot, connection, cutoff):
    """Only fully indexed, timestamped, source-present old copies qualify."""
    refresh_inventory(connection, snapshot)
    result = []
    rows = connection.execute("""SELECT f.*, max(CASE WHEN r.excluded=0 AND
        r.kind IN ('user_message','assistant_message','tool_call','tool_result') THEN r.stamp END) last_activity,
        sum(CASE WHEN r.excluded=0 AND r.kind IN ('user_message','assistant_message','tool_call','tool_result') THEN 1 ELSE 0 END) activity_count
        FROM files f LEFT JOIN records r ON r.file=f.id WHERE f.listed=1 GROUP BY f.id""")
    for file in rows:
        source = snapshot['sources'].get(file['source'], {})
        item = source.get('files', {}).get(file['path'], {})
        area_state = source.get('transfer', {}).get(file['area'])
        if (area_state not in ('ok', 'source_changed_during_pull') or
                file['status'] != 'complete' or
                file['malformed'] or file['oversized'] or file['untimestamped'] or
                not item.get('present_at_source') or not item.get('source_signature') or
                not file['activity_count'] or not file['last_activity']):
            continue
        last_activity = dt.datetime.fromisoformat(file['last_activity'])
        if last_activity >= cutoff:
            continue
        # Archive appearance itself is relevant; the first observed archive
        # baseline is not a historical transition timestamp.
        if file['area'] == 'archived_sessions':
            observed = dt.datetime.fromisoformat(item['first_observed_at'])
            if observed >= cutoff:
                continue
            if item.get('archive_observed_after') and dt.datetime.fromisoformat(item['archive_observed_after']) >= cutoff:
                continue
        relative = file['path']
        name = '/'.join(Path(relative).parts[2:])
        if not RSYNC_SAFE_PATH.fullmatch(name):
            continue
        path = cache_path(root, relative)
        if signature(path) != (file['size'], file['mtime_ns']) or file_hash(path) != file['sha256']:
            continue
        result.append({'path': relative, 'source': file['source'], 'area': file['area'],
                       'name': name, 'bytes': file['size'], 'sha256': file['sha256'],
                       'source_signature': item['source_signature'], 'last_activity': file['last_activity']})
    return result


def run(cache, config, *, days=60, timezone='UTC', apply=False, now=None):
    cutoff = cutoff_for_days(days, timezone, today=now)
    with locked_cache(cache) as root:
        snapshot = read_json(root / 'snapshot.json')
        connection = connect(root)
        try:
            candidates = plan(root, snapshot, connection, cutoff)
        finally:
            connection.close()
        orphaned = []
        for relative, marker in snapshot.get('evicted', {}).items():
            path = cache_path(root, relative)
            if not path.exists():
                continue
            parts = Path(relative).parts
            if len(parts) < 3 or parts[1] not in ('sessions', 'archived_sessions'):
                continue
            name = '/'.join(parts[2:])
            if not RSYNC_SAFE_PATH.fullmatch(name) or file_hash(path) != marker.get('sha256'):
                continue
            orphaned.append({'path': relative, 'source': parts[0], 'area': parts[1],
                             'name': name, 'bytes': private_file(path).stat().st_size,
                             'sha256': marker['sha256'], 'source_signature': marker['source_signature'],
                             'last_activity': marker['last_activity']})
        result = {'cutoff': cutoff.isoformat(), 'eligible_files': len(candidates) + len(orphaned),
                  'eligible_bytes': sum(c['bytes'] for c in candidates + orphaned),
                  'orphaned_eviction_files': len(orphaned),
                  'evicted_files': 0, 'evicted_bytes': 0, 'source_verification_gaps': {},
                  'source_status_gaps': {label: {'status': entry.get('status'), 'error': entry.get('error')}
                      for label, entry in snapshot['sources'].items() if entry.get('status') != 'ok'}}
        if not apply:
            return result
        specs = {spec['label']: spec for spec in config['sources']}
        for spec in specs.values():
            validate_source(spec)
        verified = {}
        for label in {c['source'] for c in candidates + orphaned}:
            spec = specs.get(label)
            source = snapshot['sources'].get(label)
            if spec is None or source is None or source.get('roots') != spec['roots']:
                result['source_verification_gaps'][label] = 'config_or_roots_mismatch'
                continue
            try:
                current, _ = probe_with_retry(spec, snapshot.get('exclude_sessions', []))
                if {k: current[k] for k in ('hostname','user')} != source.get('identity'):
                    raise ValueError('Source identity mismatch')
                verified[label] = current
            except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
                result['source_verification_gaps'][label] = 'current_probe_failed'
        selected = []
        for item in candidates + orphaned:
            current = verified.get(item['source'])
            if current is None:
                continue
            if current['roots'][item['area']]['status'] != 'ok':
                result['source_verification_gaps'][item['source']] = 'source_inventory_incomplete'
                continue
            if current['roots'][item['area']]['files'].get(item['name']) != item['source_signature']:
                result['source_verification_gaps'][item['source']] = 'source_file_changed_or_missing'
                continue
            selected.append(item)
        # Commit tombstones before unlinking. An interruption can leave an
        # extra local copy, never an unrecorded deletion or remote mutation.
        evicted = snapshot.setdefault('evicted', {})
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        for item in selected:
            if item['path'] not in evicted:
                evicted[item['path']] = {k: item[k] for k in ('source_signature','sha256','last_activity')}
                evicted[item['path']]['evicted_at'] = timestamp
                del snapshot['sources'][item['source']]['files'][item['path']]
        if selected:
            snapshot['observed_at'] = timestamp
            snapshot['retention_applied_at'] = timestamp
            write_json(root / 'snapshot.json', snapshot)
        for item in selected:
            path = cache_path(root, item['path'])
            if path.exists():
                private_file(path).unlink()
                result['evicted_files'] += 1
                result['evicted_bytes'] += item['bytes']
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--timezone', required=True)
    parser.add_argument('--days', type=int, default=60)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--authorized', action='store_true', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(run(args.cache, read_json(args.config), days=args.days,
                             timezone=args.timezone, apply=args.apply), indent=2))
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        parser.exit(1, 'Retention failed; no source transcript was changed.\n')


if __name__ == '__main__':
    main()
