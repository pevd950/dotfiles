#!/usr/bin/env python3
"""Classify Git configuration without emitting raw values or transport traces."""
import argparse
import os
import subprocess
from urllib.parse import urlsplit


def git_environment():
    # Git can otherwise write traces to inherited file/socket destinations even
    # when stdout/stderr are suppressed. Never create raw diagnostic artifacts.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith('GIT_TRACE') and key != 'GIT_CURL_VERBOSE'}
    # Removing variables is insufficient: trace2.*Target can enable file sinks
    # and trace2.configParams can record credential.helper verbatim.
    env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never',
               GIT_TRACE2='0', GIT_TRACE2_EVENT='0', GIT_TRACE2_PERF='0')
    return env


def query(*args):
    try:
        result = subprocess.run(['git', *args], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                env=git_environment(), timeout=15)
        return result.returncode, result.stdout.decode('utf-8', errors='replace')
    except (OSError, subprocess.TimeoutExpired):
        return 2, ''


def helper_kind(value):
    # Only exact known values pass through. Arguments and shell bodies remain
    # opaque; neither regex redaction nor shell parsing can identify all secrets.
    if not value:
        return 'reset'
    if value in {'osxkeychain', 'cache', 'store', 'manager', 'manager-core'}:
        return value
    return 'custom-shell-helper' if value.startswith('!') else 'custom-helper'


def transport_kind(value):
    try:
        scheme = urlsplit(value.strip()).scheme.lower()
    except ValueError:
        return 'unrecognized'
    if scheme in {'https', 'http', 'ssh', 'git', 'file'}:
        return scheme
    if not scheme and ':' in value and not value.startswith(('/', './', '../')):
        return 'ssh-like'
    return 'local-or-other'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('effective', 'global', 'system'), default='effective')
    parser.add_argument('--probe', action='store_true', help='try origin transport, suppressing all raw output')
    args = parser.parse_args()
    code, origin = query('remote', 'get-url', 'origin')
    print('origin transport:', transport_kind(origin) if code == 0 else 'missing-or-unavailable')
    scope = [] if args.scope == 'effective' else ['--' + args.scope]
    code, values = query('config', *scope, '--null', '--get-regexp', r'^credential(\..*)?\.helper$')
    if code == 0:
        kinds = [helper_kind(record.partition('\n')[2]) for record in values.split('\0') if record]
        print('credential helpers:', ', '.join(kinds) or 'missing')
    else:
        print('credential helpers:', 'missing' if code == 1 else 'unavailable')
    if args.probe:
        try:
            result = subprocess.run(['git', 'ls-remote', '--heads', 'origin'], stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    env=git_environment(), timeout=30)
            ok = result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        print('origin transport probe:', 'ok' if ok else 'unavailable')
        return 0 if ok else 1
    return 0 if code in (0, 1) else 1


if __name__ == '__main__':
    raise SystemExit(main())
