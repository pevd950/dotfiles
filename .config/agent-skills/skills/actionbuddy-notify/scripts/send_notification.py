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
from typing import Any


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


def shortcut_actions() -> list[dict[str, Any]]:
    with connect_db() as conn:
        shortcut_pk = find_shortcut(conn)
        data_row = conn.execute(
            "select ZDATA from ZSHORTCUTACTIONS where ZSHORTCUT = ?",
            (shortcut_pk,),
        ).fetchone()
    if not data_row:
        raise RuntimeError(f"Shortcut actions not found: {SHORTCUT_NAME}")
    actions = plistlib.loads(data_row[0])
    if not isinstance(actions, list):
        raise RuntimeError("Shortcut actions payload is malformed")
    return actions


def actionbuddy_body(actions: list[dict[str, Any]]) -> Any:
    for action in actions:
        if action.get("WFWorkflowActionIdentifier") == "codes.rambo.ActionBuddy.SendNotification":
            return action.get("WFWorkflowActionParameters", {}).get("body")
    raise RuntimeError("Send Notification shortcut does not contain ActionBuddy Send Notification action")


def contains_extension_input(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "Type" and item == "ExtensionInput":
                return True
            if key == "OutputName" and item == "Shortcut Input":
                return True
            if contains_extension_input(item):
                return True
    elif isinstance(value, list):
        return any(contains_extension_input(item) for item in value)
    elif isinstance(value, str):
        return value == "ExtensionInput"
    return False


def describe_body(body: Any) -> str:
    if isinstance(body, dict):
        if contains_extension_input(body):
            return "body_type=dict with ExtensionInput attachment"
        return "body_type=dict without ExtensionInput attachment"
    if isinstance(body, str):
        return "body_type=str"
    return f"body_type={type(body).__name__}"


def validate_shortcut_input_body() -> str:
    body = actionbuddy_body(shortcut_actions())
    description = describe_body(body)
    if not isinstance(body, dict) or not contains_extension_input(body):
        raise RuntimeError(
            f"{SHORTCUT_NAME} body must be wired to Shortcut Input; found {description}."
        )
    return description


def run_shortcut(message: str, timeout: int) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as input_file:
        input_file.write(message)
        input_file.flush()
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
    mode.add_argument("--send", action="store_true", help="Send the notification through Shortcut Input")
    parser.add_argument("--message", required=True, help="Notification body to send")
    parser.add_argument("--timeout", type=int, default=30, help="Shortcut run timeout in seconds")
    args = parser.parse_args()

    try:
        check_message(args.message)
        before = validate_shortcut_input_body()
        if args.check:
            print(f"OK: {SHORTCUT_NAME} is available; {before}; message length={len(args.message)}")
            return 0

        try:
            result = run_shortcut(args.message, args.timeout)
        except subprocess.TimeoutExpired:
            after = validate_shortcut_input_body()
            print(f"ERROR: Shortcut timed out after {args.timeout}s; {after}", file=sys.stderr)
            return 1

        after = validate_shortcut_input_body()
        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr"
            raise RuntimeError(f"Shortcut failed with exit {result.returncode}: {stderr}; {after}")

        output = result.stdout.strip() or "sent"
        print(f"OK: {output}; {after}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
