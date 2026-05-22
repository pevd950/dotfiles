#!/usr/bin/env python3
"""Send a local ActionBuddy notification through the Send Notification shortcut."""

from __future__ import annotations

import argparse
import plistlib
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


SHORTCUT_NAME = "Send Notification"
DB_PATH = Path.home() / "Library" / "Shortcuts" / "Shortcuts.sqlite"


def connect_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise RuntimeError(f"Shortcuts database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def find_shortcut(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "select Z_PK from ZSHORTCUT where ZNAME = ?",
        (SHORTCUT_NAME,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"Shortcut not found: {SHORTCUT_NAME}")
    return int(row[0])


def validate_shortcut() -> None:
    with connect_db() as conn:
        shortcut_pk = find_shortcut(conn)
        data_row = conn.execute(
            "select ZDATA from ZSHORTCUTACTIONS where ZSHORTCUT = ?",
            (shortcut_pk,),
        ).fetchone()
    if not data_row:
        raise RuntimeError(f"Shortcut actions not found: {SHORTCUT_NAME}")
    actions = plistlib.loads(data_row[0])
    has_actionbuddy = any(
        action.get("WFWorkflowActionIdentifier") == "codes.rambo.ActionBuddy.SendNotification"
        for action in actions
    )
    if not has_actionbuddy:
        raise RuntimeError("Send Notification shortcut does not contain ActionBuddy Send Notification action")
    body = next(
        action.get("WFWorkflowActionParameters", {}).get("body")
        for action in actions
        if action.get("WFWorkflowActionIdentifier") == "codes.rambo.ActionBuddy.SendNotification"
    )
    if not isinstance(body, dict):
        raise RuntimeError("ActionBuddy body is literal text; it must use Shortcut Input")
    value = body.get("Value", {})
    attachments = value.get("attachmentsByRange", {})
    if not any(
        isinstance(attachment, dict) and attachment.get("Type") == "ExtensionInput"
        for attachment in attachments.values()
    ):
        raise RuntimeError("ActionBuddy body is not wired to Shortcut Input")


def quit_shortcuts() -> None:
    subprocess.run(
        ["osascript", "-e", 'quit app "Shortcuts"'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def run_shortcut(message: str, timeout: int) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as input_file:
        input_file.write(message)
        input_path = Path(input_file.name)
    try:
        return subprocess.run(
            ["shortcuts", "run", SHORTCUT_NAME, "--input-path", str(input_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    finally:
        input_path.unlink(missing_ok=True)


def check_message(message: str) -> None:
    if not message or not message.strip():
        raise RuntimeError("Message must be non-empty")
    if len(message) > 2000:
        raise RuntimeError("Message is too long; keep notification handoffs under 2000 characters")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate message and shortcut without sending")
    mode.add_argument("--send", action="store_true", help="Patch shortcut and send the notification")
    parser.add_argument("--message", required=True, help="Notification body to send")
    parser.add_argument("--timeout", type=int, default=30, help="Shortcut run timeout in seconds")
    args = parser.parse_args()

    try:
        check_message(args.message)
        validate_shortcut()
        if args.check:
            print(f"OK: {SHORTCUT_NAME} is available; message length={len(args.message)}")
            return 0

        quit_shortcuts()
        result = run_shortcut(args.message, args.timeout)

        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr"
            raise RuntimeError(f"Shortcut failed with exit {result.returncode}: {stderr}")

        output = result.stdout.strip() or "sent"
        print(f"OK: {output}")
        return 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: Shortcut timed out after {args.timeout}s", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
