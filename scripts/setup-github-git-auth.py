#!/usr/bin/env python3
"""Check or configure unattended GitHub HTTPS access for one checkout."""

import argparse
import fnmatch
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
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


def verify_access(command, *, environment, repository, origin):
    # Public origins can be read anonymously. Exercise the selected helper as
    # well as transport, and retain its credential response only in memory.
    code, response = helper.bounded_run(
        command + ["credential", "fill"],
        input_data=("url=" + origin + "\n\n").encode(),
        environment=environment, cwd=repository, timeout=20,
    )
    fields = dict(line.split(b"=", 1) for line in response.splitlines() if b"=" in line)
    if code or not fields.get(b"username") or not fields.get(b"password"):
        raise ValueError("The selected GitHub credential helper is unavailable")
    # An accessible empty repository is valid; no matching HEAD is required.
    run(command + ["ls-remote", "origin", "HEAD"], environment=environment, cwd=repository, timeout=25)


def helper_entries(command, *, environment, repository):
    code, output = helper.bounded_run(
        command + ["config", "--includes", "--null", "--get-regexp", r"^credential(\..*)?\.helper$"],
        environment=environment, cwd=repository,
    )
    if code not in (0, 1):
        raise ValueError("Unable to inspect effective credential configuration")
    return [entry.decode().split("\n", 1) for entry in output.split(b"\0") if entry]


def github_helper_values(command, *, environment, repository):
    values = []
    for key, value in helper_entries(command, environment=environment, repository=repository):
        if key in ("credential.helper", "credential.https://github.com.helper"):
            values.append(value)
            continue
        context = urlsplit(key[len("credential."):-len(".helper")])
        # Applying a host-level route deliberately supports a narrow context.
        # Reject path/wildcard variants before mutation rather than approximating
        # Git's URL matching and overlooking helpers that receive store/erase.
        if context.hostname and fnmatch.fnmatchcase("github.com", context.hostname.lower()):
            raise ValueError("Apply does not support path-scoped or wildcard GitHub helpers; use check-only or simplify the configuration")
    return values


def configure_helpers(command, *, environment, repository, config, key, value, origin):
    """Commit the reset and helper together using Git's own config lock."""
    if config.is_symlink():
        raise ValueError("Refusing to replace a symlinked repository configuration")
    lock = config.with_name(config.name + ".lock")
    # Git writers honor this lock. Prepare both values off to the side so an
    # interruption or failure never leaves only the reset in the live config.
    with lock.open("xb"):
        candidate = None
        replaced = False
        try:
            original = config.read_bytes()
            mode = stat.S_IMODE(config.stat().st_mode)
            with tempfile.NamedTemporaryFile(dir=config.parent, prefix="github-auth-", delete=False) as stream:
                candidate = Path(stream.name)
                os.fchmod(stream.fileno(), mode)
                stream.write(original)
            for operation in (("--replace-all", key, ""), ("--add", key, value)):
                run(command + ["config", "--file", str(candidate), *operation],
                    environment=environment, cwd=repository)
            os.replace(candidate, config)
            replaced = True
            verify_helper_configuration(command, environment=environment, repository=repository,
                                        value=value, origin=origin)
        except (Exception, KeyboardInterrupt):
            if replaced:
                # Keep the config lock through verification and rollback, so a
                # failing probe cannot overwrite another Git writer's update.
                with candidate.open("xb") as stream:
                    os.fchmod(stream.fileno(), mode)
                    stream.write(original)
                os.replace(candidate, config)
            raise
        finally:
            if candidate is not None:
                candidate.unlink(missing_ok=True)
            lock.unlink(missing_ok=True)


def verify_helper_configuration(command, *, environment, repository, value, origin):
    # Includes and worktree configuration participate in the effective ordered
    # values. Every helper before the last empty value is reset by Git.
    active = []
    for entry in github_helper_values(command, environment=environment, repository=repository):
        if not entry:
            active.clear()
        else:
            active.append(entry)
    if active != [value]:
        raise ValueError("Included or worktree GitHub helpers override this checkout; resolve those settings before retrying")
    verify_access(command, environment=environment, repository=repository, origin=origin)


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
        # Prefer the host interpreter outside an activated virtual environment.
        python = tool_path(shutil.which("python3", path=os.defpath) or "python3")
        if (Path(python).parent.parent / "pyvenv.cfg").exists():
            raise ValueError("A durable host Python interpreter is required; deactivate the virtual environment")
        environment = helper.gh_environment()
        environment.update(GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/usr/bin/false", SSH_ASKPASS="/usr/bin/false")
        command = [git, "-C", str(repository)]
        top = Path(run(command + ["rev-parse", "--show-toplevel"], environment=environment, cwd=repository))
        if top.resolve() != repository:
            raise ValueError("Pass the checkout root as --repository")
        git_paths = run(command + ["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
                        environment=environment, cwd=repository).splitlines()
        if args.apply:
            worktrees = run(command + ["worktree", "list", "--porcelain"],
                            environment=environment, cwd=repository)
            has_siblings = sum(line.startswith("worktree ") for line in worktrees.splitlines()) > 1
            if has_siblings or Path(git_paths[0]).resolve() != Path(git_paths[1]).resolve():
                raise ValueError("Apply requires a standalone checkout without linked worktrees; they share repository configuration")
        origin = run(command + ["remote", "get-url", "origin"], environment=environment, cwd=repository)
        url = urlsplit(origin)
        if (url.scheme != "https" or url.netloc != "github.com" or url.query or url.fragment
                or len(url.path.strip("/").split("/")) != 2):
            raise ValueError("Origin must be a credential-free https://github.com/OWNER/REPO URL")
        # Check the existing stored identity before changing any configuration.
        run([gh, "api", "user", "--jq", ".login"], environment=environment, cwd=repository)
        if args.apply:
            key = "credential.https://github.com.helper"
            github_helper_values(command, environment=environment, repository=repository)
            candidate = "!" + shlex.join([python, str(HELPER_SOURCE.resolve()), "--gh", gh])
            verify_access(command + ["-c", key + "=", "-c", key + "=" + candidate],
                          environment=environment, repository=repository, origin=origin)
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
                configure_helpers(command, environment=environment, repository=repository,
                                  config=Path(git_paths[1]) / "config", key=key, value=value, origin=origin)
            else:
                verify_helper_configuration(command, environment=environment, repository=repository,
                                            value=value, origin=origin)
            print("Checkout GitHub helper configured.")
        else:
            verify_access(command, environment=environment, repository=repository, origin=origin)
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
