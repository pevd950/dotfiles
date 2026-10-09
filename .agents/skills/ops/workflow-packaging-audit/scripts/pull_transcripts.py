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

from transcript_cache import cache_path, file_hash, locked_cache, private_dir, private_file, read_json, signature, write_json

# Only metadata is returned by the identity/inventory probe. Paths are explicit
# approved transcript roots, never a home-directory or configuration copy.
PROBE = r'''
import getpass,hashlib,json,os,pathlib,socket,stat,sys
request=json.load(sys.stdin); result={'hostname':socket.gethostname(),'user':getpass.getuser(),'roots':{}}
for area,raw in request['roots'].items():
 p=pathlib.Path(raw)
 if not p.is_absolute() or any(x.is_symlink() for x in (p,*p.parents)) or not p.is_dir():
  result['roots'][area]={'status':'missing_or_unsafe','files':{}};continue
 files={};gaps=[];hash_files=set(request.get('hash_files',{}).get(area,[]))
 for base,dirs,names in os.walk(p,followlinks=False,onerror=lambda _:gaps.append('unreadable_directory')):
  unsafe=[d for d in dirs if pathlib.Path(base,d).is_symlink()]
  gaps.extend('symlink_directory' for _ in unsafe);dirs[:]=[d for d in dirs if d not in unsafe]
  for name in names:
   if not name.endswith('.jsonl'):continue
   q=pathlib.Path(base,name)
   try:
    s=q.lstat()
    if not stat.S_ISREG(s.st_mode):gaps.append('nonregular_transcript');continue
    name=str(q.relative_to(p)); item={'size':s.st_size,'mtime_ns':s.st_mtime_ns}
    if name in hash_files:
     digest=hashlib.sha256()
     with q.open('rb') as handle:
      opened=os.fstat(handle.fileno())
      if (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns,opened.st_ctime_ns)!=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns):
       gaps.append('changed_hash_target');continue
      for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
      end=os.fstat(handle.fileno())
     final=q.lstat()
     proof=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
     if proof(s)!=proof(end) or proof(s)!=proof(final):gaps.append('changed_hash_target');continue
     item['sha256']=digest.hexdigest()
    files[name]=item
   except OSError:gaps.append('unreadable_transcript')
 result['roots'][area]={'status':'ok' if not gaps else 'partial','files':files,'gaps':gaps}
print(json.dumps(result))
'''
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=10', '-o', 'ConnectionAttempts=1', '-T']
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')
RSYNC_SAFE_PATH = re.compile(r'[A-Za-z0-9_./-]+\Z')


class ProbeUnavailable(ValueError):
    """A transport failure, distinct from a source identity mismatch."""


def validate_source(spec):
    for field in ('label',):
        if not isinstance(spec.get(field), str) or not LABEL.fullmatch(spec[field]):
            raise ValueError('Invalid source label')
    if spec['label'].lower() in {'snapshot.json', 'index.sqlite3', 'index.sqlite3-journal', 'index.sqlite3-wal', 'index.sqlite3-shm', 'review-ledger.json'}:
        raise ValueError('Reserved cache-control source label')
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
    payload = json.dumps({'roots': spec['roots'], 'exclude_sessions': exclude, 'hash_files': spec.get('_hash_files', {})})
    command = (SSH + [spec['ssh'], 'python3 -c ' + shlex.quote(PROBE)]
               if spec.get('ssh') else [sys.executable, '-c', PROBE])
    result = subprocess.run(command, input=payload, capture_output=True, text=True, timeout=30)
    if result.returncode:
        if spec.get('ssh') and result.returncode == 255:
            raise ProbeUnavailable('ssh_probe_unavailable')
        raise ValueError('Source identity/inventory probe command failed')
    value = json.loads(result.stdout)
    if value.get('hostname', '').casefold() not in {h.casefold() for h in spec['hostnames']} or value.get('user') != spec['user']:
        raise ValueError('Source identity mismatch')
    return value


def probe_with_retry(spec, exclude):
    """Retry one transient metadata probe; never retry a transfer or change identity."""
    try:
        return probe(spec, exclude), 0
    except (subprocess.TimeoutExpired, ProbeUnavailable):
        return probe(spec, exclude), 1


def rsync_command(spec, area, destination, exclude, skipped=()):
    root = spec['roots'][area]
    origin = spec['ssh'] + ':' + shlex.quote(root + '/') if spec.get('ssh') else root + '/'
    command = ['rsync', '-rt', '--checksum', '--delay-updates', '--timeout=60']
    if spec.get('ssh'):
        command += ['-e', shlex.join(SSH)]
    command += ['--exclude=/' + name for name in sorted(skipped)]
    return command + ['--exclude=.~tmp~/', '--include=*/', '--include=*.jsonl', '--exclude=*', '--', origin, str(destination) + '/']


def pull(cache, config):
    if not isinstance(config, dict):
        raise ValueError('Expected a configuration object')
    sources = config.get('sources', [])
    if not isinstance(sources, list) or not sources or not all(isinstance(s, dict) for s in sources):
        raise ValueError('Supply a nonempty source list')
    for spec in sources:
        validate_source(spec)
    if len({s['label'].casefold() for s in sources}) != len(sources):
        raise ValueError('Supply uniquely labeled approved sources')
    for spec in sources:
        if spec.get('ssh') is None:
            destination = Path(cache).resolve()
            for source in spec['roots'].values():
                origin = Path(source).resolve()
                if destination.is_relative_to(origin) or origin.is_relative_to(destination):
                    raise ValueError('Cache and local transcript roots must not overlap')
    exclude = config.get('exclude_sessions', [])
    if not isinstance(exclude, list) or not all(isinstance(x, str) and LABEL.fullmatch(x) for x in exclude):
        raise ValueError('Invalid session exclusions')
    with locked_cache(cache) as root:
        metadata = root / 'snapshot.json'
        previous = read_json(metadata) if metadata.exists() else {'sources': {}}
        prior_labels = {label.casefold(): label for label in previous['sources']}
        if any(spec['label'].casefold() in prior_labels and prior_labels[spec['label'].casefold()] != spec['label'] for spec in sources):
            raise ValueError('Source label differs only by case from prior cache identity')
        evicted = dict(previous.get('evicted', {}))
        snapshot = {'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'exclude_sessions': exclude, 'sources': {s['label']: {**previous['sources'].get(s['label'], {}),
                        'status': 'not_attempted', 'error': None} for s in sources},
                    'evicted': evicted,
                    'archive_history': 'First observation is a baseline; earlier archive/unarchive transitions are unknown.'}
        write_json(metadata, snapshot)
        for spec in sources:
            label = spec['label']
            old = previous['sources'].get(label, {})
            entry = {**old, 'status': 'unavailable', 'error': None}
            snapshot['sources'][label] = entry
            try:
                phase = 'initial_probe'
                coverage_through = dt.datetime.now(dt.timezone.utc).isoformat()
                # Hash only tombstoned sources, including same-metadata rewrites.
                hash_files = {'sessions': [], 'archived_sessions': []}
                for relative in evicted:
                    parts = Path(relative).parts
                    if len(parts) >= 3 and parts[0] == label and parts[1] in hash_files:
                        name = '/'.join(parts[2:])
                        if RSYNC_SAFE_PATH.fullmatch(name):
                            hash_files[parts[1]].append(name)
                probe_spec = {**spec, '_hash_files': hash_files}
                before, retries = probe_with_retry(probe_spec, exclude)
                identity = {k: before[k] for k in ('hostname', 'user')}
                if old.get('identity') not in (None, identity) or old.get('roots') not in (None, spec['roots']):
                    raise ValueError('Source label was reused; use a new cache label')
                entry['identity'] = identity
                entry['probe_timeout_retries'] = retries
                skipped = {'sessions': set(), 'archived_sessions': set()}
                for relative, marker in list(evicted.items()):
                    parts = Path(relative).parts
                    if len(parts) < 3 or parts[0] != label or parts[1] not in skipped:
                        continue
                    cache_path(root, relative)
                    area, name = parts[1], '/'.join(parts[2:])
                    source_item = before['roots'][area]['files'].get(name)
                    if (source_item and RSYNC_SAFE_PATH.fullmatch(name) and
                            {k: source_item[k] for k in ('size', 'mtime_ns')} == marker.get('source_signature') and
                            source_item.get('sha256') == marker.get('sha256') and
                            marker.get('exclude_sessions') is not None and
                            sorted(marker['exclude_sessions']) == sorted(exclude)):
                        skipped[area].add(name)
                    elif source_item:
                        # A resumed or otherwise changed old chat returns to the hot cache.
                        del evicted[relative]
                source_dir = private_dir(root / label)
                # Publish invalidation before rsync can replace any cached bytes.
                # Keep prior hashes only in the private in-memory recovery input.
                entry.update(files={}, status='transferring')
                write_json(metadata, snapshot)
                transfer = {}
                for area in ('sessions', 'archived_sessions'):
                    if before['roots'][area]['status'] != 'ok':
                        transfer[area] = 'source_inventory_incomplete'
                        continue
                    phase = 'rsync_' + area
                    destination = private_dir(source_dir / area)
                    # Never let a prior cache symlink redirect rsync writes.
                    for base, dirs, files in os.walk(destination):
                        for name in dirs + files:
                            cache_path(root, str((Path(base) / name).relative_to(root)))
                    result = subprocess.run(rsync_command(spec, area, destination, exclude, skipped[area]),
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
                phase = 'final_probe'
                after, extra_retries = probe_with_retry(probe_spec, exclude)
                entry['probe_timeout_retries'] += extra_retries
                inventory_completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
                inventory = {}
                for area in ('sessions', 'archived_sessions'):
                    copied = transfer[area] == 'ok'
                    now_files = after['roots'][area]['files']
                    if before['roots'][area] != after['roots'][area]:
                        transfer[area] = 'source_changed_during_pull'
                    if any(after['roots'][area]['files'].get(name) != before['roots'][area]['files'].get(name)
                           for name in skipped[area]):
                        transfer[area] = 'evicted_source_changed_during_pull'
                    for relative, marker in evicted.items():
                        parts = Path(relative).parts
                        if parts[:2] == (label, area):
                            marker['present_at_source'] = '/'.join(parts[2:]) in now_files
                    directory = source_dir / area
                    if not directory.exists():
                        continue
                    for path in sorted(directory.rglob('*.jsonl')):
                        if '.~tmp~' in path.relative_to(directory).parts:
                            continue  # Uncommitted rsync staging is not a source copy.
                        relative = str(path.relative_to(root))
                        cache_path(root, relative)
                        if relative in evicted:
                            continue  # A prior interrupted eviction left an orphan copy.
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
                            'source_signature': {k: now_files[name][k] for k in ('size', 'mtime_ns')} if present else None,
                            'first_observed_at': prior.get('first_observed_at', snapshot['observed_at']),
                            'archive_observed_after': (prior.get('archive_observed_after') or
                                (old.get('last_successful_pull') if area == 'archived_sessions' and not prior and present else None)),
                            'archive_observed_through': (prior.get('archive_observed_through') or
                                (inventory_completed_at if area == 'archived_sessions' and not prior and present else None))}
                    # Missing new source files are explicit transfer gaps; old
                    # cached files remain available and are labeled as retained.
                    if any(str(Path(label, area, name)) not in inventory and name not in skipped[area]
                           for name in now_files):
                        transfer[area] = 'cache_missing_source_files'
                # Once identical bytes are recovered in a verified archive copy,
                # the absent active path no longer represents missing history.
                if transfer.get('archived_sessions') == 'ok':
                    recovered = {item['sha256'] for item in inventory.values()
                                 if item['area'] == 'archived_sessions' and item['present_at_source']}
                    for relative, marker in list(evicted.items()):
                        if (Path(relative).parts[:2] == (label, 'sessions') and
                                marker.get('present_at_source') is False and marker.get('sha256') in recovered):
                            orphan = cache_path(root, relative)
                            if orphan.exists():
                                first = signature(orphan)
                                if file_hash(orphan) != marker['sha256'] or signature(orphan) != first:
                                    transfer['sessions'] = 'unverified_eviction_orphan'
                                    continue
                                # Finish the already-authorized, interrupted eviction
                                # only after its identical archive copy is verified.
                                private_file(orphan).unlink()
                            del evicted[relative]
                entry.update(files=inventory, transfer=transfer, roots=spec['roots'],
                             coverage_through=coverage_through, inventory_completed_at=inventory_completed_at,
                             status='ok' if all(v == 'ok' for v in transfer.values()) else 'partial')
                if entry['status'] == 'ok':
                    entry['last_successful_pull'] = dt.datetime.now(dt.timezone.utc).isoformat()
            except subprocess.TimeoutExpired:
                entry.update(status='unavailable', error=phase + '_timeout')
            except ProbeUnavailable:
                entry.update(status='unavailable', error=phase + '_ssh_unavailable')
            except (OSError, ValueError, KeyError, TypeError):
                entry.update(status='unavailable', error='source_unavailable_or_invalid')
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
