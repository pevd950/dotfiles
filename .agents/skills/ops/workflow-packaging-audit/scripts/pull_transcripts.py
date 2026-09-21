#!/usr/bin/env python3
"""Explicit private transcript pulls using existing SSH authentication and rsync."""
import argparse
import datetime as dt
import getpass
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import stat

from transcript_cache import cache_path, file_hash, locked_cache, private_dir, read_json, signature, write_json

# Only metadata is returned by the identity/inventory probe. Paths are explicit
# approved transcript roots, never a home-directory or configuration copy.
PROBE = r'''
import getpass,json,os,pathlib,socket,stat,sys
request=json.loads(sys.argv[1]); result={'hostname':socket.gethostname(),'user':getpass.getuser(),'roots':{}}
for area,raw in request['roots'].items():
 p=pathlib.Path(raw)
 if not p.is_absolute() or any(x.is_symlink() for x in (p,*p.parents)) or not p.is_dir():
  result['roots'][area]={'status':'missing_or_unsafe','files':{}};continue
 files={};gaps=[]
 for base,dirs,names in os.walk(p,followlinks=False,onerror=lambda _:gaps.append('unreadable_directory')):
  unsafe=[d for d in dirs if pathlib.Path(base,d).is_symlink()]
  gaps.extend('symlink_directory' for _ in unsafe);dirs[:]=[d for d in dirs if d not in unsafe]
  for name in names:
   if not name.endswith('.jsonl'):continue
   q=pathlib.Path(base,name)
   try:
    s=q.lstat()
    if not stat.S_ISREG(s.st_mode):gaps.append('nonregular_transcript');continue
    files[str(q.relative_to(p))]={'size':s.st_size,'mtime_ns':s.st_mtime_ns}
   except OSError:gaps.append('unreadable_transcript')
 result['roots'][area]={'status':'ok' if not gaps else 'partial','files':files,'gaps':gaps}
print(json.dumps(result))
'''
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=10', '-o', 'ConnectionAttempts=1', '-T']
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')


def validate_source(spec):
    for field in ('label',):
        if not isinstance(spec.get(field), str) or not LABEL.fullmatch(spec[field]):
            raise ValueError('Invalid source label')
    if spec.get('ssh') is not None and not LABEL.fullmatch(spec['ssh']):
        raise ValueError('Use an existing SSH host alias')
    if not isinstance(spec.get('hostnames'), list) or not spec['hostnames'] or not all(isinstance(h, str) and h for h in spec['hostnames']):
        raise ValueError('Expected hostnames required')
    if not isinstance(spec.get('user'), str) or not spec['user']:
        raise ValueError('Expected source user required')
    if set(spec.get('roots', {})) != {'sessions', 'archived_sessions'}:
        raise ValueError('Supply exactly the two approved transcript roots')
    for area, raw in spec['roots'].items():
        p = Path(raw)
        if '\0' in raw or not p.is_absolute() or '..' in p.parts or p.name != area or p.parent.name != '.codex':
            raise ValueError('Only explicit .codex transcript roots are supported')


def probe(spec, exclude):
    payload = json.dumps({'roots': spec['roots'], 'exclude_sessions': exclude})
    command = (SSH + [spec['ssh'], 'python3 -c ' + shlex.quote(PROBE) + ' ' + shlex.quote(payload)]
               if spec.get('ssh') else [sys.executable, '-c', PROBE, payload])
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('Source identity/inventory probe failed')
    value = json.loads(result.stdout)
    if value.get('hostname', '').casefold() not in {h.casefold() for h in spec['hostnames']} or value.get('user') != spec['user']:
        raise ValueError('Source identity mismatch')
    return value


def rsync_command(spec, area, destination, exclude):
    root = spec['roots'][area]
    origin = spec['ssh'] + ':' + shlex.quote(root + '/') if spec.get('ssh') else root + '/'
    command = ['rsync', '-rt', '--checksum', '--delay-updates', '--timeout=60']
    if spec.get('ssh'):
        command += ['-e', shlex.join(SSH)]
    return command + ['--exclude=.~tmp~/', '--include=*/', '--include=*.jsonl', '--exclude=*', '--', origin, str(destination) + '/']


def pull(cache, config):
    sources = config.get('sources', [])
    if not sources or len({s['label'] for s in sources}) != len(sources):
        raise ValueError('Supply uniquely labeled approved sources')
    for spec in sources:
        validate_source(spec)
    exclude = config.get('exclude_sessions', [])
    if not isinstance(exclude, list) or not all(isinstance(x, str) and LABEL.fullmatch(x) for x in exclude):
        raise ValueError('Invalid session exclusions')
    with locked_cache(cache) as root:
        metadata = root / 'snapshot.json'
        previous = read_json(metadata) if metadata.exists() else {'sources': {}}
        snapshot = {'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'exclude_sessions': exclude, 'sources': {s['label']: {**previous['sources'].get(s['label'], {}),
                        'status': 'not_attempted', 'error': None} for s in sources},
                    'archive_history': 'First observation is a baseline; earlier archive/unarchive transitions are unknown.'}
        write_json(metadata, snapshot)
        for spec in sources:
            label = spec['label']
            old = previous['sources'].get(label, {})
            entry = {**old, 'status': 'unavailable', 'error': None}
            snapshot['sources'][label] = entry
            try:
                coverage_through = dt.datetime.now(dt.timezone.utc).isoformat()
                before = probe(spec, exclude)
                identity = {k: before[k] for k in ('hostname', 'user')}
                if old.get('identity') not in (None, identity) or old.get('roots') not in (None, spec['roots']):
                    raise ValueError('Source label was reused; use a new cache label')
                entry['identity'] = identity
                source_dir = private_dir(root / label)
                transfer = {}
                for area in ('sessions', 'archived_sessions'):
                    if before['roots'][area]['status'] != 'ok':
                        transfer[area] = 'source_inventory_incomplete'
                        continue
                    destination = private_dir(source_dir / area)
                    # Never let a prior cache symlink redirect rsync writes.
                    for base, dirs, files in os.walk(destination):
                        for name in dirs + files:
                            cache_path(root, str((Path(base) / name).relative_to(root)))
                    result = subprocess.run(rsync_command(spec, area, destination, exclude),
                                            capture_output=True, timeout=3600)
                    # Apple openrsync accepts symbolic --chmod but can retain
                    # source modes. The enclosing 0700 cache stays private;
                    # normalize only owned cache copies before inventorying.
                    for base, dirs, files in os.walk(destination):
                        for path in [Path(base), *(Path(base) / n for n in dirs + files)]:
                            info = path.lstat()
                            if info.st_uid != os.getuid() or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
                                raise ValueError('Unsafe cache entry')
                            path.chmod(0o700 if stat.S_ISDIR(info.st_mode) else 0o600)
                    transfer[area] = 'ok' if result.returncode == 0 else 'rsync_incomplete'
                after = probe(spec, exclude)
                inventory_completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
                inventory = {}
                for area in ('sessions', 'archived_sessions'):
                    copied = transfer[area] == 'ok'
                    now_files = after['roots'][area]['files']
                    if before['roots'][area] != after['roots'][area]:
                        transfer[area] = 'source_changed_during_pull'
                    directory = source_dir / area
                    if not directory.exists():
                        continue
                    for path in sorted(directory.rglob('*.jsonl')):
                        if '.~tmp~' in path.relative_to(directory).parts:
                            continue  # Uncommitted rsync staging is not a source copy.
                        relative = str(path.relative_to(root))
                        cache_path(root, relative)
                        name = str(path.relative_to(directory))
                        prior = old.get('files', {}).get(relative, {})
                        present = name in now_files
                        if not prior and (not copied or (not present and name not in before['roots'][area]['files'])):
                            transfer[area] = 'unattributed_cache_file'
                            continue
                        first = signature(path)
                        digest = file_hash(path)
                        if signature(path) != first:
                            raise ValueError('Cache changed during inventory')
                        if not copied and prior and digest != prior.get('sha256'):
                            transfer[area] = 'unverified_cache_change'
                            continue
                        inventory[relative] = {
                            'area': area, 'sha256': digest, 'size': first[0], 'mtime_ns': first[1],
                            'present_at_source': present,
                            'first_observed_at': prior.get('first_observed_at', snapshot['observed_at']),
                            'archive_observed_after': (prior.get('archive_observed_after') or
                                (old.get('last_successful_pull') if area == 'archived_sessions' and not prior and present else None))}
                    # Missing new source files are explicit transfer gaps; old
                    # cached files remain available and are labeled as retained.
                    if any(str(Path(label, area, name)) not in inventory for name in now_files):
                        transfer[area] = 'cache_missing_source_files'
                entry.update(files=inventory, transfer=transfer, roots=spec['roots'],
                             coverage_through=coverage_through, inventory_completed_at=inventory_completed_at,
                             status='ok' if all(v == 'ok' for v in transfer.values()) else 'partial')
                if entry['status'] == 'ok':
                    entry['last_successful_pull'] = dt.datetime.now(dt.timezone.utc).isoformat()
            except subprocess.TimeoutExpired:
                entry['error'] = 'source_timeout'
            except (OSError, ValueError, KeyError, TypeError):
                entry['error'] = 'source_unavailable_or_invalid'
            write_json(metadata, snapshot)
        return {label: {'status': entry['status'], 'error': entry.get('error'),
                        'cached_files': len(entry.get('files', {})), 'transfer': entry.get('transfer', {})}
                for label, entry in snapshot['sources'].items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--authorized', action='store_true', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(pull(args.cache, read_json(args.config)), indent=2))
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(1, 'Pull failed; inspect private configuration and source availability.\n')


if __name__ == '__main__':
    main()
