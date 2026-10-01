#!/usr/bin/env python3
"""Move untracked Zsh additions after pulling the reorganized dotfiles.

No file contents are read or copied. A collision aborts before any changes;
renames preserve modes, symlinks, and plugin repositories. Keep a compatibility
link for applications that still refer to the former custom directory.
"""

import argparse
import os
from pathlib import Path
import sys


def present(path):
    return path.exists() or path.is_symlink()


def plan_moves(source, target):
    moves, directories = [], []

    def visit(old, new):
        if not present(new):
            moves.append((old, new))
        elif old.is_dir() and not old.is_symlink() and new.is_dir() and not new.is_symlink():
            directories.append((old, old.stat().st_mode & 0o777))
            for child in sorted(old.iterdir()):
                visit(child, new / child.name)
        else:
            raise ValueError("Conflicting paths in old and new custom directories; resolve them before migrating.")

    visit(source, target)
    return moves, directories


def relative_links(source, target):
    """Plan link targets so moving deeper does not change external references."""
    links = []
    for parent, directories, files in os.walk(source, followlinks=False):
        for name in directories + files:
            old = Path(parent) / name
            if not old.is_symlink():
                continue
            original = os.readlink(old)
            if os.path.isabs(original):
                continue
            referenced = Path(os.path.abspath(old.parent / original))
            if referenced.is_relative_to(source):
                referenced = target / referenced.relative_to(source)
            new = target / old.relative_to(source)
            replacement = os.path.relpath(referenced, new.parent)
            if replacement != original:
                links.append((new, original, replacement))
    return links


def migrate(home, apply=False):
    source = home / ".zshrc_custom"
    target = home / ".config/zsh/custom"
    if not target.is_dir() or target.is_symlink():
        raise ValueError("Pull the reorganized dotfiles before running this migration.")
    if source.is_symlink():
        if source.resolve() != target.resolve():
            raise ValueError("The legacy custom path is a link to a different directory; resolve it first.")
        return 0
    if present(source) and not source.is_dir():
        raise ValueError("The legacy custom path is not a directory; resolve it first.")
    moves, directories = plan_moves(source, target) if source.exists() else ([], [])
    links = relative_links(source, target) if source.exists() else []
    if source.exists() and source.stat().st_dev != target.stat().st_dev:
        raise ValueError("The old and new directories must be on the same filesystem for safe renames.")
    if not apply:
        return len(moves)
    completed, removed, rewritten = [], [], []
    try:
        for old, new in moves:
            # Recheck after planning so a new collision cannot be overwritten.
            if present(new):
                raise ValueError("A destination appeared during migration; no files will be overwritten.")
            old.rename(new)
            completed.append((old, new))
        for link, original, replacement in links:
            link.unlink()
            rewritten.append((link, original))
            link.symlink_to(replacement)
        for directory, mode in reversed(directories):
            directory.rmdir()
            removed.append((directory, mode))
        source.symlink_to(".config/zsh/custom", target_is_directory=True)
    except BaseException:
        failures = []

        def recover(path, operation, *args, **kwargs):
            try:
                operation(*args, **kwargs)
            except OSError as error:
                failures.append(f"{path}: {error}")

        if source.is_symlink():
            recover(source, source.unlink)
        for link, original in reversed(rewritten):
            if link.is_symlink():
                recover(link, link.unlink)
            # os.symlink also works if a failed Path.symlink_to triggered recovery.
            recover(link, os.symlink, original, link)
        for directory, mode in reversed(removed):
            recover(directory, directory.mkdir, mode=mode)
            recover(directory, os.chmod, directory, mode)
        for old, new in reversed(completed):
            recover(old, new.rename, old)
        if failures:
            print("Recovery incomplete; these paths need manual attention:\n" +
                  "\n".join(failures), file=sys.stderr)
        raise
    return len(moves)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="move additions and create the compatibility link")
    args = parser.parse_args()
    try:
        count = migrate(Path.home(), args.apply)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Migration stopped: {error}\n")
    print(f"{'Migrated' if args.apply else 'Would migrate'} {count} local additions; "
          + ("legacy path remains compatible." if args.apply else "run with --apply to proceed."))


if __name__ == "__main__":
    main()
