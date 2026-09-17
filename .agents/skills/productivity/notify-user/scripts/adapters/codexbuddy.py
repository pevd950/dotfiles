"""Codex Buddy adapter: probe Host/MCP and refuse any invented send bypass."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Callable, TYPE_CHECKING

from . import ProviderResult, ValidationError

if TYPE_CHECKING:
    from send_notification import Notification, ProviderSpec

TITLE_MAX_BYTES = 120
SUBTITLE_MAX_BYTES = 160
BODY_MAX_BYTES = 560
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
MCP_BINARIES = ("codex-buddy-mcp",)
MCP_CONFIG_HINTS = (
    Path.home() / ".codex" / "config.toml",
    Path.home() / ".cursor" / "mcp.json",
)
HOST_MARKERS = ("codex-buddy-mcp", "codex-buddy", "buddy_send_custom_notification", "buddy_host_status")
APPROVAL_GATE = (
    "approval_gate: buddy_send_custom_notification requires explicit user approval; "
    "this adapter does not invoke Buddy MCP or invent a Host send path"
)


def utf8_bytes(value: str) -> int:
    return len(value.encode("utf-8"))


def validate_fields(notification: Notification) -> None:
    if utf8_bytes(notification.title) > TITLE_MAX_BYTES:
        raise ValidationError("title exceeds Codex Buddy's 120-byte limit")
    if utf8_bytes(notification.subtitle) > SUBTITLE_MAX_BYTES:
        raise ValidationError("subtitle exceeds Codex Buddy's 160-byte limit")
    if utf8_bytes(notification.message) > BODY_MAX_BYTES:
        raise ValidationError("message exceeds Codex Buddy's 560-byte body limit")
    namespace = notification.caller_namespace_id.strip() or "notify-user"
    if not ID_PATTERN.match(namespace):
        raise ValidationError("callerNamespaceID must match Buddy's stable ID pattern")
    if notification.notification_id and not ID_PATTERN.match(notification.notification_id):
        raise ValidationError("notificationID must match Buddy's stable ID pattern")
    destination = notification.destination.strip()
    if destination and not (
        destination.startswith("https://") or destination.startswith("codexbuddy:")
    ):
        raise ValidationError("destination must be HTTPS or a portable codexbuddy URL")


def detect_host(which: Callable[[str], str | None] = shutil.which, home: Path | None = None) -> bool:
    if any(which(name) for name in MCP_BINARIES):
        return True
    roots = [home] if home is not None else [Path.home()]
    candidates = list(MCP_CONFIG_HINTS)
    if home is not None:
        candidates = [home / ".codex" / "config.toml", home / ".cursor" / "mcp.json"]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(marker in text for marker in HOST_MARKERS):
            return True
    for root in roots:
        plugin = root / ".codex" / "plugins" / "codex-buddy"
        if plugin.exists():
            return True
    return False


def run(
    mode: str,
    notification: Notification,
    spec: ProviderSpec,
    host_probe: Callable[[], bool] | None = None,
    **_kwargs,
) -> ProviderResult:
    try:
        validate_fields(notification)
    except ValidationError as exc:
        return ProviderResult("codexbuddy", "failed", str(exc))

    probe = host_probe or detect_host
    if not probe():
        return ProviderResult("codexbuddy", "skipped", "Codex Buddy Host/MCP unavailable")

    if mode == "check":
        return ProviderResult(
            "codexbuddy",
            "checked",
            "Host/MCP looks present; fields valid; send still requires explicit user approval "
            "for buddy_send_custom_notification",
        )
    return ProviderResult("codexbuddy", "skipped", APPROVAL_GATE)
