#!/usr/bin/env python3
"""Regression tests for ActionBuddy Send Notification helper sqlite access."""

from __future__ import annotations

import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import send_notification as helper  # noqa: E402


TITLE_UUID = "title-uuid"
SUBTITLE_UUID = "subtitle-uuid"
BODY_UUID = "body-uuid"


def valid_actions() -> list[dict]:
    return [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.detect.dictionary",
            "WFWorkflowActionParameters": {
                "WFInput": {"Type": "ExtensionInput", "OutputName": "Shortcut Input"},
            },
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
            "WFWorkflowActionParameters": {"WFDictionaryKey": "title", "UUID": TITLE_UUID},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
            "WFWorkflowActionParameters": {"WFDictionaryKey": "subtitle", "UUID": SUBTITLE_UUID},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
            "WFWorkflowActionParameters": {"WFDictionaryKey": "body", "UUID": BODY_UUID},
        },
        {
            "WFWorkflowActionIdentifier": "codes.rambo.ActionBuddy.SendNotification",
            "WFWorkflowActionParameters": {
                "ShowWhenRun": False,
                "title": {"Type": "ActionOutput", "OutputUUID": TITLE_UUID},
                "subtitle": {"Type": "ActionOutput", "OutputUUID": SUBTITLE_UUID},
                "body": {"Type": "ActionOutput", "OutputUUID": BODY_UUID},
            },
        },
    ]


def run_main(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(sys, "argv", ["send_notification.py", *argv]),
        patch("sys.stdout", stdout),
        patch("sys.stderr", stderr),
    ):
        code = helper.main()
    return code, stdout.getvalue(), stderr.getvalue()


CHECK_ARGS = [
    "--check",
    "--title",
    "Codex",
    "--subtitle",
    "Ready",
    "--message",
    "For the user from Codex: sqlite TCC check.",
]
SEND_ARGS = [
    "--send",
    "--title",
    "Codex",
    "--subtitle",
    "Ready",
    "--message",
    "For the user from Codex: sqlite TCC send.",
]


class SqliteAccessClassificationTests(unittest.TestCase):
    def test_tcc_and_sandbox_errors_are_soft_access_failures(self):
        cases = [
            sqlite3.OperationalError("unable to open database file"),
            PermissionError("Operation not permitted"),
            OSError("authorization denied"),
            RuntimeError("Shortcuts database not found: /tmp/Shortcuts.sqlite"),
        ]
        for exc in cases:
            with self.subTest(exc=str(exc)):
                self.assertTrue(helper.is_db_unreadable(exc))

    def test_wiring_errors_are_not_soft_access_failures(self):
        self.assertFalse(
            helper.is_db_unreadable(RuntimeError("Send Notification must keep Show When Run disabled"))
        )


class StrictWiringTests(unittest.TestCase):
    def test_check_ok_when_sqlite_actions_are_readable_and_wired(self):
        with (
            patch.object(helper, "shortcut_actions", return_value=valid_actions()),
            patch.object(helper, "shortcut_is_listed", return_value=True),
        ):
            code, stdout, stderr = run_main(CHECK_ARGS)
        self.assertEqual(code, 0, stderr)
        self.assertIn("OK:", stdout)
        self.assertIn("title/subtitle/body wired", stdout)
        self.assertNotIn("ERROR:", stderr)

    def test_check_skips_when_sqlite_is_readable_but_shortcuts_is_missing(self):
        with (
            patch.object(helper, "shortcut_actions", return_value=valid_actions()),
            patch.object(helper, "shortcut_is_listed", return_value=False),
        ):
            code, stdout, stderr = run_main(CHECK_ARGS)
        self.assertEqual(code, 1, stdout + stderr)
        self.assertIn("shortcuts executable not found", stderr)
        self.assertNotIn("OK:", stdout)

    def test_check_hard_fails_when_db_is_readable_but_wiring_is_wrong(self):
        actions = [
            {
                "WFWorkflowActionIdentifier": "codes.rambo.ActionBuddy.SendNotification",
                "WFWorkflowActionParameters": {"ShowWhenRun": False, "body": "literal"},
            }
        ]
        with patch.object(helper, "shortcut_actions", return_value=actions):
            code, stdout, stderr = run_main(CHECK_ARGS)
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", stderr)
        self.assertNotIn("OK:", stdout)


class SqliteSoftFailTests(unittest.TestCase):
    def test_check_soft_fails_when_sqlite_tcc_blocks_and_shortcut_is_listed(self):
        def fake_run(cmd, **_kwargs):
            if cmd[:2] == ["shortcuts", "list"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="Send Notification\nOther\n", stderr="")
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(
                helper,
                "shortcut_actions",
                side_effect=sqlite3.OperationalError("unable to open database file"),
            ),
            patch.object(helper.subprocess, "run", side_effect=fake_run),
        ):
            code, stdout, stderr = run_main(CHECK_ARGS)

        combined = stdout + stderr
        self.assertEqual(code, 0, combined)
        self.assertNotIn("ERROR:", stderr)
        self.assertTrue("OK:" in stdout or "WARN:" in combined)
        self.assertIn("Send Notification", combined)
        self.assertRegex(combined.lower(), r"unable to open database file|wiring check skipped|unreadable")

    def test_check_soft_fails_when_database_missing_and_shortcuts_list_fails(self):
        def fake_run(cmd, **_kwargs):
            if cmd[:2] == ["shortcuts", "list"]:
                raise FileNotFoundError("shortcuts")
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(
                helper,
                "shortcut_actions",
                side_effect=RuntimeError("Shortcuts database not found: /missing/Shortcuts.sqlite"),
            ),
            patch.object(helper.subprocess, "run", side_effect=fake_run),
        ):
            code, stdout, stderr = run_main(CHECK_ARGS)

        combined = stdout + stderr
        self.assertEqual(code, 0, combined)
        self.assertNotIn("ERROR:", stderr)
        self.assertIn("WARN:", combined)

    def test_send_still_runs_shortcut_when_sqlite_is_unreadable(self):
        captured: dict[str, object] = {}

        def fake_run(cmd, **_kwargs):
            if cmd[:2] == ["shortcuts", "list"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="Send Notification\n", stderr="")
            if cmd[:3] == ["shortcuts", "run", "Send Notification"]:
                captured["cmd"] = list(cmd)
                input_path = Path(cmd[cmd.index("--input-path") + 1])
                captured["payload"] = json.loads(input_path.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(cmd, 0, stdout="Notification sent!\n", stderr="")
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(
                helper,
                "shortcut_actions",
                side_effect=PermissionError("Operation not permitted"),
            ),
            patch.object(helper.subprocess, "run", side_effect=fake_run),
        ):
            code, stdout, stderr = run_main(SEND_ARGS)

        combined = stdout + stderr
        self.assertEqual(code, 0, combined)
        self.assertNotIn("ERROR:", stderr)
        self.assertIn("OK:", stdout)
        self.assertIn("Notification sent!", stdout)
        self.assertEqual(captured["cmd"][:3], ["shortcuts", "run", "Send Notification"])
        self.assertIn("--input-path", captured["cmd"])
        self.assertEqual(
            captured["payload"],
            {
                "title": "Codex",
                "subtitle": "Ready",
                "body": "For the user from Codex: sqlite TCC send.",
            },
        )

    def test_send_reports_shortcut_failure_even_when_sqlite_is_unreadable(self):
        def fake_run(cmd, **_kwargs):
            if cmd[:2] == ["shortcuts", "list"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="Send Notification\n", stderr="")
            if cmd[:3] == ["shortcuts", "run", "Send Notification"]:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="shortcut boom")
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(
                helper,
                "shortcut_actions",
                side_effect=PermissionError("Operation not permitted"),
            ),
            patch.object(helper.subprocess, "run", side_effect=fake_run),
        ):
            code, stdout, stderr = run_main(SEND_ARGS)

        self.assertEqual(code, 1, stdout + stderr)
        self.assertIn("Shortcut failed with exit 1", stderr)
        self.assertIn("shortcut boom", stderr)

    def test_send_errors_when_shortcuts_executable_is_missing(self):
        with (
            patch.object(
                helper,
                "shortcut_actions",
                side_effect=RuntimeError("Shortcuts database not found: /missing/Shortcuts.sqlite"),
            ),
            patch.object(helper, "run_shortcut", side_effect=FileNotFoundError("shortcuts")),
        ):
            code, stdout, stderr = run_main(SEND_ARGS)

        self.assertEqual(code, 1, stdout + stderr)
        self.assertIn("shortcuts executable not found", stderr)
        self.assertNotIn("Shortcut failed with exit", stderr)


class ReadonlyDatabaseTests(unittest.TestCase):
    def test_connect_db_opens_sqlite_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "Shortcuts.sqlite"
            seed = sqlite3.connect(db_path)
            seed.execute("create table ZSHORTCUT (Z_PK integer, ZNAME text)")
            seed.execute("insert into ZSHORTCUT values (1, 'Send Notification')")
            seed.commit()
            seed.close()

            with patch.object(helper, "DB_PATH", db_path):
                with helper.connect_db() as conn:
                    with self.assertRaises(sqlite3.Error):
                        conn.execute("insert into ZSHORTCUT values (2, 'patched')")
                    conn.rollback()
                    row = conn.execute("select ZNAME from ZSHORTCUT where Z_PK = 1").fetchone()
            verify = sqlite3.connect(db_path)
            names = [item[0] for item in verify.execute("select ZNAME from ZSHORTCUT").fetchall()]
            verify.close()
        self.assertEqual(row, ("Send Notification",))
        self.assertEqual(names, ["Send Notification"])


if __name__ == "__main__":
    unittest.main()
