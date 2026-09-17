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
    "No such file or directory",
)
SQLITE_SOFT_MARKERS = (
    "unable to open database file",
    "Operation not permitted",
    "authorization denied",
    "Shortcuts database unreadable",
    "sqlite wiring check skipped",
)
INDETERMINATE_MARKERS = ("WARN:", "timed out")


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
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(notification.timeout, 5),
        )
    except FileNotFoundError as exc:
        return ProviderResult("actionbuddy", "skipped", f"helper unavailable: {exc}")
    except subprocess.TimeoutExpired:
        return ProviderResult("actionbuddy", "indeterminate", "helper timed out")

    status = classify(completed.returncode, completed.stdout, completed.stderr)
    detail = (completed.stdout.strip() or completed.stderr.strip() or f"exit {completed.returncode}")
    if status == "ok":
        status = "checked" if mode == "check" else "sent"
    return ProviderResult("actionbuddy", status, detail)
