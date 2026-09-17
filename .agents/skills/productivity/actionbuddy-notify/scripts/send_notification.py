#!/usr/bin/env python3
"""Send a local ActionBuddy notification through the Send Notification shortcut.

Supported notification content fields are title, subtitle, and message/body.
Use all three fields when validating setup or helper changes.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SHORTCUT_NAME = "Send Notification"
DB_PATH = Path.home() / "Library" / "Shortcuts" / "Shortcuts.sqlite"
DB_UNREADABLE_MARKERS = (
    "unable to open database file",
    "authorization denied",
    "operation not permitted",
    "permission denied",
    "database not found",
    "shortcuts database not found",
    "shortcuts database unreadable",
)


def is_db_unreadable(exc: BaseException) -> bool:
    if isinstance(exc, PermissionError):
        return True
    text = str(exc).lower()
    return any(marker in text for marker in DB_UNREADABLE_MARKERS)


def connect_db() -> sqlite3.Connection:
    try:
        exists = DB_PATH.exists()
    except OSError as exc:
        raise RuntimeError(f"Shortcuts database unreadable: {exc}") from exc
    if not exists:
        raise RuntimeError(f"Shortcuts database not found: {DB_PATH}")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only = ON")
        return conn
    except (sqlite3.Error, OSError) as exc:
        raise RuntimeError(f"Shortcuts database unreadable: {exc}") from exc


def find_shortcut(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "select Z_PK from ZSHORTCUT where ZNAME = ?",
        (SHORTCUT_NAME,),
    ).fetchone()
    if not row:
        raise RuntimeError(f"Shortcut not found: {SHORTCUT_NAME}")
    return int(row[0])


def shortcut_actions() -> list[dict[str, Any]]:
    try:
        with connect_db() as conn:
            shortcut_pk = find_shortcut(conn)
            data_row = conn.execute(
                "select ZDATA from ZSHORTCUTACTIONS where ZSHORTCUT = ?",
                (shortcut_pk,),
            ).fetchone()
    except (sqlite3.Error, OSError) as exc:
        raise RuntimeError(f"Shortcuts database unreadable: {exc}") from exc
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


def actionbuddy_action(actions: list[dict[str, Any]]) -> dict[str, Any]:
    for action in actions:
        if action.get("WFWorkflowActionIdentifier") == "codes.rambo.ActionBuddy.SendNotification":
            return action
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


def contains_action_output(value: Any, output_uuid: str) -> bool:
    if isinstance(value, dict):
        if value.get("Type") == "ActionOutput" and value.get("OutputUUID") == output_uuid:
            return True
        return any(contains_action_output(item, output_uuid) for item in value.values())
    if isinstance(value, list):
        return any(contains_action_output(item, output_uuid) for item in value)
    return False


def describe_body(body: Any) -> str:
    if isinstance(body, dict):
        if contains_extension_input(body):
            return "body_type=dict with ExtensionInput attachment"
        return "body_type=dict without ExtensionInput attachment"
    if isinstance(body, str):
        return "body_type=str"
    return f"body_type={type(body).__name__}"


def dictionary_value_uuids(actions: list[dict[str, Any]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for action in actions:
        if action.get("WFWorkflowActionIdentifier") != "is.workflow.actions.getvalueforkey":
            continue
        params = action.get("WFWorkflowActionParameters", {})
        key = params.get("WFDictionaryKey")
        uuid = params.get("UUID")
        if isinstance(key, str) and isinstance(uuid, str):
            values[key] = uuid
    return values


def validate_structured_shortcut(actions: list[dict[str, Any]]) -> str:
    notification = actionbuddy_action(actions)
    params = notification.get("WFWorkflowActionParameters", {})
    if params.get("ShowWhenRun") is not False:
        raise RuntimeError(f"{SHORTCUT_NAME} must keep Show When Run disabled")

    for action in actions:
        if (
            action.get("WFWorkflowActionIdentifier") == "is.workflow.actions.detect.dictionary"
            and contains_extension_input(action.get("WFWorkflowActionParameters", {}).get("WFInput"))
        ):
            break
    else:
        raise RuntimeError(f"{SHORTCUT_NAME} must parse a JSON Shortcut Input dictionary")

    values = dictionary_value_uuids(actions)
    missing = [key for key in ("title", "subtitle", "body") if key not in values]
    if missing:
        raise RuntimeError(
            f"{SHORTCUT_NAME} must extract title, subtitle, and body from Shortcut Input; missing {', '.join(missing)}"
        )

    for param_name, key in (("title", "title"), ("subtitle", "subtitle"), ("body", "body")):
        if not contains_action_output(params.get(param_name), values[key]):
            raise RuntimeError(f"{SHORTCUT_NAME} {param_name} must be wired to the {key!r} Shortcut Input field")

    return "title/subtitle/body wired from JSON Shortcut Input; ShowWhenRun=false"


def validate_shortcut_input_body() -> str:
    actions = shortcut_actions()
    try:
        return validate_structured_shortcut(actions)
    except RuntimeError as structured_error:
        body = actionbuddy_body(actions)
        if isinstance(body, dict) and contains_extension_input(body):
            raise RuntimeError(
                f"{SHORTCUT_NAME} still uses the legacy body-only Shortcut Input contract; "
                "update it to parse title, subtitle, and body from JSON Shortcut Input"
            ) from structured_error

    description = describe_body(body)
    raise RuntimeError(
        f"{SHORTCUT_NAME} body must be wired to structured Shortcut Input; found {description}."
    )


def shortcut_is_listed() -> bool:
    try:
        result = subprocess.run(
            ["shortcuts", "list"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    names = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return SHORTCUT_NAME in names


def try_validate_shortcut_input_body() -> tuple[str, bool, bool | None]:
    """Return (detail, strict, listed).

    strict=True means Shortcuts.sqlite was readable and wiring was validated.
    listed is set only when sqlite was unreadable and `shortcuts list` was consulted.
    """
    try:
        return validate_shortcut_input_body(), True, None
    except Exception as exc:
        if not is_db_unreadable(exc):
            raise
        listed = shortcut_is_listed()
        warning = f"sqlite wiring check skipped ({exc})"
        if listed:
            return f"{warning}; {SHORTCUT_NAME} listed by shortcuts", False, True
        return f"{warning}; {SHORTCUT_NAME} not confirmed via shortcuts list", False, False


def notification_payload(title: str, subtitle: str, message: str) -> str:
    return json.dumps(
        {
            "title": title.strip() or "ActionBuddy",
            "subtitle": subtitle.strip(),
            "body": message,
        },
        ensure_ascii=False,
    )


def run_shortcut(title: str, subtitle: str, message: str, timeout: int) -> subprocess.CompletedProcess[str]:
    payload = notification_payload(title, subtitle, message)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as input_file:
        input_file.write(payload)
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


def check_message(message: str, title: str, subtitle: str) -> None:
    if not message or not message.strip():
        raise RuntimeError("Message must be non-empty")
    if len(message) > 2000:
        raise RuntimeError("Message is too long; keep notification handoffs under 2000 characters")
    if len(title) > 120:
        raise RuntimeError("Title is too long; keep notification titles under 120 characters")
    if len(subtitle) > 180:
        raise RuntimeError("Subtitle is too long; keep notification subtitles under 180 characters")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Example validation with all content fields: "
            "--check --title Codex --subtitle Validation --message 'For the user from Codex: test notification.'"
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate message and shortcut without sending")
    mode.add_argument("--send", action="store_true", help="Send the notification through Shortcut Input")
    parser.add_argument("--message", required=True, help="Notification body to send; maps to JSON field 'body'")
    parser.add_argument("--title", default="ActionBuddy", help="Notification title; maps to JSON field 'title'")
    parser.add_argument("--subtitle", default="Codex", help="Notification subtitle; maps to JSON field 'subtitle'")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Shortcut run timeout in seconds; not notification content",
    )
    args = parser.parse_args()

    try:
        check_message(args.message, args.title, args.subtitle)
        before, strict, listed = try_validate_shortcut_input_body()
        lengths = (
            f"title length={len(args.title)}; subtitle length={len(args.subtitle)}; "
            f"message length={len(args.message)}"
        )
        if args.check:
            if strict:
                print(f"OK: {SHORTCUT_NAME} is available; {before}; {lengths}")
                return 0
            if listed:
                print(f"OK: {SHORTCUT_NAME} is listed; {before}; {lengths}")
                return 0
            print(f"WARN: {SHORTCUT_NAME} sqlite wiring unavailable; {before}; {lengths}", file=sys.stderr)
            return 0

        try:
            result = run_shortcut(args.title, args.subtitle, args.message, args.timeout)
        except subprocess.TimeoutExpired:
            after, _, _ = try_validate_shortcut_input_body()
            print(
                f"WARN: Shortcut timed out after {args.timeout}s; delivery may have succeeded; {after}",
                file=sys.stderr,
            )
            return 0
        except FileNotFoundError:
            after, _, _ = try_validate_shortcut_input_body()
            print(
                f"ERROR: shortcuts executable not found; ActionBuddy is unavailable; {after}",
                file=sys.stderr,
            )
            return 1

        after, _, _ = try_validate_shortcut_input_body()
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
