#!/usr/bin/env python3
"""Check or configure unattended GitHub HTTPS access for one checkout."""

import argparse
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
from urllib.parse import urlsplit


HELPER_SOURCE = Path(__file__).with_name("github-credential-helper.py")
spec = importlib.util.spec_from_file_location("github_credential_helper", HELPER_SOURCE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def tool_path(name):
    path = shutil.which(name)
    if not path:
        raise ValueError(f"Required tool unavailable: {name}")
    # Keep stable package-manager symlinks instead of versioned Cellar paths.
    return os.path.abspath(path)


def run(command, *, environment, cwd, timeout=20):
    code, output = helper.bounded_run(command, environment=environment, cwd=cwd, timeout=timeout)
    if code:
        raise ValueError("Command failed; no credential or provider output was retained")
    return output.decode().strip()


def verify_access(command, *, environment, repository):
    # Public origins can be read anonymously. Exercise the selected helper as
    # well as transport, and retain its credential response only in memory.
    code, response = helper.bounded_run(
        command + ["credential", "fill"],
        input_data=b"protocol=https\nhost=github.com\n\n",
        environment=environment, cwd=repository, timeout=20,
    )
    fields = dict(line.split(b"=", 1) for line in response.splitlines() if b"=" in line)
    if code or not fields.get(b"username") or not fields.get(b"password"):
        raise ValueError("The selected GitHub credential helper is unavailable")
    # An accessible empty repository is valid; no matching HEAD is required.
    run(command + ["ls-remote", "origin"], environment=environment, cwd=repository, timeout=25)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--git", default="git", help="Git executable, including Xcode's bundled Git")
    parser.add_argument("--apply", action="store_true", help="Install the bounded helper and pin this checkout")
    args = parser.parse_args()
    try:
        repository = args.repository.resolve(strict=True)
        git = tool_path(args.git)
        gh = tool_path("gh")
        python = tool_path("python3")
        environment = helper.gh_environment()
        environment.update(GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/usr/bin/false", SSH_ASKPASS="/usr/bin/false")
        command = [git, "-C", str(repository)]
        top = Path(run(command + ["rev-parse", "--show-toplevel"], environment=environment, cwd=repository))
        if top.resolve() != repository:
            raise ValueError("Pass the checkout root as --repository")
        git_paths = run(command + ["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
                        environment=environment, cwd=repository).splitlines()
        if args.apply and Path(git_paths[0]).resolve() != Path(git_paths[1]).resolve():
            raise ValueError("Apply requires a standalone checkout; linked worktrees share repository configuration")
        origin = run(command + ["remote", "get-url", "origin"], environment=environment, cwd=repository)
        url = urlsplit(origin)
        if (url.scheme != "https" or url.netloc != "github.com" or url.query or url.fragment
                or len(url.path.strip("/").split("/")) != 2):
            raise ValueError("Origin must be a credential-free https://github.com/OWNER/REPO URL")
        # Check the existing stored identity before changing any configuration.
        run([gh, "api", "user", "--jq", ".login"], environment=environment, cwd=repository)
        if args.apply:
            key = "credential.https://github.com.helper"
            candidate = "!" + shlex.join([python, str(HELPER_SOURCE.resolve()), "--gh", gh])
            verify_access(command + ["-c", key + "=", "-c", key + "=" + candidate],
                          environment=environment, repository=repository)
            destination = Path.home() / ".local/libexec/dotfiles/github-credential-helper.py"
            if not destination.parent.is_dir():
                destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_symlink():
                raise ValueError("Refusing to replace a symlinked credential helper")
            source = HELPER_SOURCE.read_bytes()
            if not destination.exists() or destination.read_bytes() != source:
                # Never install a partially written helper while Git is using it.
                temporary = destination.with_name(destination.name + f".{os.getpid()}.tmp")
                try:
                    with temporary.open("xb") as stream:
                        os.chmod(temporary, 0o700)
                        stream.write(source)
                    os.replace(temporary, destination)
                finally:
                    temporary.unlink(missing_ok=True)
            if stat.S_IMODE(destination.stat().st_mode) != 0o700:
                os.chmod(destination, 0o700)
            value = "!" + shlex.join([python, str(destination), "--gh", gh])
            current_code, current = helper.bounded_run(
                command + ["config", "--local", "--get-all", key],
                environment=environment, cwd=repository,
            )
            expected = ("\n" + value + "\n").encode()
            if current_code not in (0, 1):
                raise ValueError("Unable to read checkout credential configuration")
            if current != expected:
                # An empty first helper resets inherited helpers. Keep other
                # hosts, the remote URL, and global/home configuration intact.
                run(command + ["config", "--local", "--replace-all", key, ""], environment=environment, cwd=repository)
                run(command + ["config", "--local", "--add", key, value], environment=environment, cwd=repository)
            print("Checkout GitHub helper configured.")
        else:
            verify_access(command, environment=environment, repository=repository)
        print("PASS: GitHub identity, selected credential helper and origin verified with prompts disabled and no shell token exports.")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        if isinstance(error, subprocess.TimeoutExpired):
            message = "Authentication check timed out; only this probe's child processes were stopped"
        elif isinstance(error, PermissionError):
            message = "Permission denied configuring the local helper or checkout; use a session allowed to write those paths"
        elif isinstance(error, OSError):
            message = "A required local file or executable is unavailable"
        else:
            message = str(error)
        print(f"FAIL: {message}.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
