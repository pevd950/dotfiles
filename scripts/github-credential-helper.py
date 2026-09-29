#!/usr/bin/env python3
"""Bound GitHub credential lookup without displaying or retaining credentials."""

import argparse
import os
import signal
import subprocess
import sys


def gh_environment():
    # GUI processes do not inherit interactive shell token exports. Use the
    # provisioned gh identity consistently, including in terminal preflights.
    environment = {
        key: os.environ[key]
        for key in (
            "HOME", "USER", "XDG_CONFIG_HOME", "GH_CONFIG_DIR", "DBUS_SESSION_BUS_ADDRESS",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "all_proxy", "no_proxy",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "GIT_SSL_CAINFO", "GIT_SSL_CAPATH",
            "CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE",
        )
        if key in os.environ
    }
    environment.update(PATH="/usr/bin:/bin:/usr/sbin:/sbin", GH_PROMPT_DISABLED="1")
    return environment


def bounded_run(command, *, input_data=None, timeout=15, environment=None, cwd=None):
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=environment, cwd=cwd, start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(input_data, timeout=timeout)
    except subprocess.TimeoutExpired:
        # Kill only the process group created by this invocation, including a
        # blocked credential-provider child. Never retain provider diagnostics.
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return process.returncode, stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gh", required=True)
    parser.add_argument("operation", choices=("get", "store", "erase", "capability"))
    args = parser.parse_args()
    # Git broadcasts store/erase to helpers. This adapter uses gh's existing
    # identity; it must never write another Keychain item or revoke that identity.
    if args.operation != "get":
        return 0
    request = sys.stdin.buffer.read(65537)
    try:
        fields = dict(line.split(b"=", 1) for line in request.splitlines() if line)
        allowed = fields.get(b"protocol") == b"https" and fields.get(b"host") in (
            b"github.com", b"gist.github.com",
        )
        if len(request) > 65536 or not allowed:
            raise ValueError("unsupported credential request")
        code, response = bounded_run(
            [args.gh, "auth", "git-credential", "get"], input_data=request,
            environment=gh_environment(),
        )
        credentials = dict(line.split(b"=", 1) for line in response.splitlines() if line)
        if code or not credentials.get(b"username") or not credentials.get(b"password"):
            raise ValueError("GitHub credential unavailable")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        # Git's quit flag prevents fallback to another helper or an askpass UI.
        sys.stdout.write("quit=1\n\n")
        sys.stderr.write("GitHub authentication unavailable; run the unattended Git preflight.\n")
        return 0
    # This is Git's private credential pipe, never a diagnostic/log destination.
    sys.stdout.buffer.write(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
