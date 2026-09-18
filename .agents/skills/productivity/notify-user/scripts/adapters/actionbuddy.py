"""ActionBuddy adapter: wrap the existing macOS Shortcuts helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import ProviderResult

if TYPE_CHECKING:
    from send_notification import Notification, ProviderSpec

UNAVAILABLE_MARKERS = (
    "Shortcuts database not found",
    "shortcuts executable not found",
)
SQLITE_SOFT_MARKERS = (
    "unable to open database file",
    "Operation not permitted",
    "authorization denied",
    "Shortcuts database unreadable",
    "sqlite wiring check skipped",
)
INDETERMINATE_MARKERS = ("WARN:", "timed out")
# Two `shortcuts list` probes (10s each) plus helper cleanup around `shortcuts run`.
HELPER_OVERHEAD_SECONDS = 30


def default_helper() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "actionbuddy-notify"
        / "scripts"
        / "send_notification.py"
    )


def classify(returncode: int, stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}"
    if returncode == 0 and "OK:" in stdout:
        return "ok"
    if returncode != 0 and (
        "Shortcut failed with exit" in text or "is not listed by shortcuts" in text
    ):
        return "failed"
    if "timed out" in text:
        return "indeterminate"
    if any(marker in text for marker in UNAVAILABLE_MARKERS):
        return "skipped"
    if any(marker in text for marker in SQLITE_SOFT_MARKERS):
        return "indeterminate"
    if any(marker in text for marker in INDETERMINATE_MARKERS):
        return "indeterminate"
    if returncode == 0:
        return "ok"
    return "failed"


def run(mode: str, notification: Notification, spec: ProviderSpec, **_kwargs) -> ProviderResult:
    helper = Path(spec.helper) if spec.helper else default_helper()
    if not helper.is_file():
        return ProviderResult("actionbuddy", "failed", f"helper not found: {helper}")
    timeout = max(notification.timeout, 1)
    command = [
        sys.executable,
        str(helper),
        f"--{mode}",
        "--title",
        notification.title,
        "--subtitle",
        notification.subtitle,
        "--message",
        notification.message,
        "--timeout",
        str(timeout),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + HELPER_OVERHEAD_SECONDS,
        )
    except FileNotFoundError as exc:
        return ProviderResult("actionbuddy", "skipped", f"helper unavailable: {exc}")
    except subprocess.TimeoutExpired:
        return ProviderResult("actionbuddy", "indeterminate", "helper timed out")

    status = classify(completed.returncode, completed.stdout, completed.stderr)
    if status == "ok":
        reported = "checked" if mode == "check" else "sent"
        return ProviderResult("actionbuddy", reported, "helper ok")
    if status == "skipped":
        return ProviderResult("actionbuddy", status, "ActionBuddy unavailable")
    if status == "indeterminate":
        return ProviderResult("actionbuddy", status, "ActionBuddy indeterminate")
    return ProviderResult("actionbuddy", "failed", f"helper failed (exit {completed.returncode})")
