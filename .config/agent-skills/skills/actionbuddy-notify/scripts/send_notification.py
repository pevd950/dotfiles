#!/usr/bin/env python3
"""Send a local ActionBuddy notification through the Send Notification shortcut."""

from __future__ import annotations

import argparse
import plistlib
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


SHORTCUT_NAME = "Send Notification"
DB_PATH = Path.home() / "Library" / "Shortcuts" / "Shortcuts.sqlite"
READY_MESSAGE = "ActionBuddy notification relay ready."
MAC_EPOCH_OFFSET = 978307200


def mac_time() -> float:
    return time.time() - MAC_EPOCH_OFFSET


def build_actions(message: str) -> bytes:
    send_uuid = "E4708B92-5AB2-498F-ADCF-2C3878AA8D7B"
    output_uuid = "D4D835D6-8350-4B1D-80F4-093D80AAA4F7"
    actions = [
        {
            "WFWorkflowActionIdentifier": "codes.rambo.ActionBuddy.SendNotification",
            "WFWorkflowActionParameters": {
                "AppIntentDescriptor": {
                    "AppIntentIdentifier": "SendNotification",
                    "BundleIdentifier": "codes.rambo.ActionBuddy",
                    "Name": "ActionBuddy",
                    "TeamIdentifier": "8C7439RJLG",
                },
                "body": message,
                "UUID": send_uuid,
            },
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.output",
            "WFWorkflowActionParameters": {
                "UUID": output_uuid,
                "WFOutput": {
                    "Value": {
                        "attachmentsByRange": {
                            "{0, 1}": {
                                "OutputName": "Send Notification",
                                "OutputUUID": send_uuid,
                                "Type": "ActionOutput",
                            }
                        },
                        "string": "\ufffc",
                    },
                    "WFSerializationType": "WFTextTokenString",
                },
            },
        },
    ]
    return plistlib.dumps(actions, fmt=plistlib.FMT_BINARY)


def connect_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise RuntimeError(f"Shortcuts database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def find_shortcut(conn: sqlite3.Connection) -> tuple[int, int]:
    row = conn.execute(
        "select Z_PK, ZACTIONS from ZSHORTCUT where ZNAME = ?",
        (SHORTCUT_NAME,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"Shortcut not found: {SHORTCUT_NAME}")
    return int(row[0]), int(row[1])


def patch_shortcut(message: str) -> None:
    with connect_db() as conn:
        shortcut_pk, actions_pk = find_shortcut(conn)
        data = build_actions(message)
        conn.execute(
            "update ZSHORTCUTACTIONS set ZDATA = ? where Z_PK = ?",
            (data, actions_pk),
        )
        conn.execute(
            """
            update ZSHORTCUT
            set ZACTIONCOUNT = 2,
                ZHASSHORTCUTINPUTVARIABLES = 0,
                ZACTIONSDESCRIPTION = ?,
                ZMODIFICATIONDATE = ?
            where Z_PK = ?
            """,
            ("Send Notification and Stop and Output", mac_time(), shortcut_pk),
        )
        conn.commit()


def validate_shortcut() -> None:
    with connect_db() as conn:
        shortcut_pk, _ = find_shortcut(conn)
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


def quit_shortcuts() -> None:
    subprocess.run(
        ["osascript", "-e", 'quit app "Shortcuts"'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def run_shortcut(timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["shortcuts", "run", SHORTCUT_NAME],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


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

        patch_shortcut(args.message)
        quit_shortcuts()
        result = run_shortcut(args.timeout)
        patch_shortcut(READY_MESSAGE)

        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr"
            raise RuntimeError(f"Shortcut failed with exit {result.returncode}: {stderr}")

        output = result.stdout.strip() or "sent"
        print(f"OK: {output}")
        return 0
    except subprocess.TimeoutExpired:
        patch_shortcut(READY_MESSAGE)
        print(f"ERROR: Shortcut timed out after {args.timeout}s", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
