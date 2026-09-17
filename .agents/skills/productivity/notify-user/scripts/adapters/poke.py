"""Poke adapter: fold structured fields into the existing webhook helper."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import ProviderResult

if TYPE_CHECKING:
    from send_notification import Notification, ProviderSpec


def default_helper() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "poke-notify"
        / "scripts"
        / "send_notification.py"
    )


def fold_message(notification: Notification) -> str:
    head = " — ".join(part for part in (notification.title.strip(), notification.subtitle.strip()) if part)
    body = notification.message.strip()
    if not head:
        return body
    if body.startswith(head):
        return body
    return f"{head}: {body}"


def run(mode: str, notification: Notification, spec: ProviderSpec, **_kwargs) -> ProviderResult:
    if not os.environ.get("POKE_API_KEY", "").strip():
        return ProviderResult("poke", "skipped", "POKE_API_KEY is not set")

    helper = Path(spec.helper) if spec.helper else default_helper()
    command = [
        sys.executable,
        str(helper),
        f"--{mode}",
        "--message",
        fold_message(notification),
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
        return ProviderResult("poke", "failed", f"helper unavailable: {exc}")
    except subprocess.TimeoutExpired:
        return ProviderResult("poke", "indeterminate", "helper timed out")

    detail = completed.stdout.strip() or completed.stderr.strip() or f"exit {completed.returncode}"
    api_key = os.environ.get("POKE_API_KEY", "")
    if api_key and api_key in detail:
        detail = detail.replace(api_key, "$POKE_API_KEY")
    if completed.returncode == 0:
        return ProviderResult("poke", "checked" if mode == "check" else "sent", detail)
    return ProviderResult("poke", "failed", detail)
