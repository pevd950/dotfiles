#!/usr/bin/env python3
"""Fan out a structured user notification to enabled providers.

Callers should use this entrypoint instead of ActionBuddy, Poke, or Buddy MCP
for routine handoffs. Provider order and enable flags live in config, not in
workflow skills.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from adapters import ProviderResult, ValidationError
from adapters import actionbuddy, codexbuddy, poke

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TITLE = "Codex"
DEFAULT_SUBTITLE = "Codex"
DEFAULT_NAMESPACE = "notify-user"
RUNNERS: dict[str, Callable[..., ProviderResult]] = {
    "actionbuddy": actionbuddy.run,
    "poke": poke.run,
    "codexbuddy": codexbuddy.run,
}


@dataclass(frozen=True)
class Notification:
    title: str
    subtitle: str
    message: str
    destination: str = ""
    caller_namespace_id: str = DEFAULT_NAMESPACE
    notification_id: str = ""
    timeout: int = 30


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    enabled: bool
    helper: str | None = None


def bundled_config_path() -> Path:
    return SKILL_DIR / "config" / "providers.example.toml"


def user_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "notify-user" / "providers.toml"


def resolve_config_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("NOTIFY_USER_CONFIG")
    if env:
        return Path(env)
    user = user_config_path()
    if user.is_file():
        return user
    return bundled_config_path()


def _parse_toml_scalar(raw: str):
    value = raw.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        if not _quoted_scalar_is_well_formed(value, '"', allow_escape=True):
            raise ValidationError(f"invalid TOML scalar: {raw!r}")
        return _unescape_toml_basic(value[1:-1])
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        if "'" in value[1:-1]:
            raise ValidationError(f"invalid TOML scalar: {raw!r}")
        return value[1:-1]
    raise ValidationError(f"invalid TOML scalar: {raw!r}")


def _quoted_scalar_is_well_formed(value: str, quote: str, *, allow_escape: bool) -> bool:
    inner = value[1:-1]
    if not allow_escape:
        return quote not in inner
    escaped = False
    for char in inner:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == quote:
            return False
    return True


def _strip_toml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if in_double:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_double = False
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = True
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _unescape_toml_basic(value: str) -> str:
    out: list[str] = []
    replacements = {"b": "\b", "t": "\t", "n": "\n", "f": "\f", "r": "\r", '"': '"', "\\": "\\"}
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            raise ValidationError("invalid TOML escape: trailing backslash")
        code = value[index]
        if code in replacements:
            out.append(replacements[code])
            index += 1
            continue
        if code in {"u", "U"}:
            width = 4 if code == "u" else 8
            hexdigits = value[index + 1 : index + 1 + width]
            if len(hexdigits) != width or any(
                digit not in "0123456789abcdefABCDEF" for digit in hexdigits
            ):
                raise ValidationError(f"invalid TOML unicode escape: \\{code}{hexdigits}")
            ordinal = int(hexdigits, 16)
            if ordinal > 0x10FFFF or 0xD800 <= ordinal <= 0xDFFF:
                raise ValidationError(f"invalid TOML unicode escape: \\{code}{hexdigits}")
            out.append(chr(ordinal))
            index += 1 + width
            continue
        raise ValidationError(f"invalid TOML escape: \\{code}")
    return "".join(out)


def load_providers(path: Path) -> list[ProviderSpec]:
    text = path.read_text(encoding="utf-8")
    providers: list[ProviderSpec] = []
    current: dict[str, object] | None = None
    for raw in text.splitlines():
        line = _strip_toml_comment(raw).strip()
        if not line:
            continue
        if line == "[[providers]]":
            if current is not None:
                providers.append(_provider_from_mapping(current))
            current = {}
            continue
        if current is None:
            raise ValidationError(f"{path}: keys must appear under [[providers]]")
        if "=" not in line:
            raise ValidationError(f"{path}: invalid line {raw!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        if key in current:
            raise ValidationError(f"{path}: duplicate key {key!r}")
        current[key] = _parse_toml_scalar(value)
    if current is not None:
        providers.append(_provider_from_mapping(current))
    if not providers:
        raise ValidationError(f"{path}: no [[providers]] entries")
    seen: set[str] = set()
    for provider in providers:
        if provider.id in seen:
            raise ValidationError(f"{path}: duplicate provider id {provider.id!r}")
        seen.add(provider.id)
    return providers


def _provider_from_mapping(mapping: dict[str, object]) -> ProviderSpec:
    provider_id = mapping.get("id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValidationError("provider id is required")
    unknown = sorted(set(mapping) - {"id", "enabled", "helper"})
    if unknown:
        raise ValidationError(f"{provider_id}: unknown keys: {', '.join(unknown)}")
    enabled = mapping.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValidationError(f"{provider_id}: enabled must be a boolean")
    helper = mapping.get("helper")
    if helper is not None and not isinstance(helper, str):
        raise ValidationError(f"{provider_id}: helper must be a string")
    return ProviderSpec(id=provider_id.strip(), enabled=enabled, helper=helper)


def validate_notification(notification: Notification) -> None:
    if not notification.message or not notification.message.strip():
        raise ValidationError("message must be a non-empty string")
    if not notification.title.strip():
        raise ValidationError("title must be a non-empty string")


def aggregate_status(results: Iterable[ProviderResult], mode: str) -> str:
    items = list(results)
    attempted = [item for item in items if item.status != "disabled"]
    if mode == "check":
        if any(item.status == "failed" for item in attempted):
            return "failed"
        return "checked"

    sent = [item for item in attempted if item.status == "sent"]
    indeterminate = [item for item in attempted if item.status == "indeterminate"]
    failed = [item for item in attempted if item.status == "failed"]
    if sent:
        first = attempted[0] if attempted else None
        if first is not None and first.status == "failed":
            return "fallback sent"
        return "sent"
    if indeterminate and not failed:
        return "indeterminate"
    if indeterminate and not sent:
        return "indeterminate"
    return "failed"


def run_fanout(
    mode: str,
    notification: Notification,
    providers: list[ProviderSpec],
    runners: dict[str, Callable[..., ProviderResult]] | None = None,
) -> tuple[list[ProviderResult], str]:
    validate_notification(notification)
    dispatch = runners or RUNNERS
    results: list[ProviderResult] = []
    for spec in providers:
        if not spec.enabled:
            results.append(
                ProviderResult(spec.id, "disabled", "disabled in config (not a silent fallback)")
            )
            continue
        runner = dispatch.get(spec.id)
        if runner is None:
            results.append(ProviderResult(spec.id, "failed", "unknown provider id"))
            continue
        try:
            results.append(runner(mode, notification, spec))
        except Exception:
            results.append(ProviderResult(spec.id, "failed", "provider raised an unexpected error"))
    return results, aggregate_status(results, mode)


def redact_detail(detail: str) -> str:
    text = detail
    home = str(Path.home())
    if home:
        text = text.replace(home, "$HOME")
    api_key = os.environ.get("POKE_API_KEY", "")
    if api_key:
        text = text.replace(api_key, "$POKE_API_KEY")
    return text


def format_report(results: list[ProviderResult], status: str) -> str:
    lines = [f"{item.provider}: {item.status} — {redact_detail(item.detail)}" for item in results]
    lines.append(f"notification_status: {status}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate and probe enabled providers without sending")
    mode.add_argument("--send", action="store_true", help="Fan out to every enabled provider that can send")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Notification title")
    parser.add_argument("--subtitle", default=DEFAULT_SUBTITLE, help="Notification subtitle / reason")
    parser.add_argument("--message", required=True, help="Notification body")
    parser.add_argument("--destination", default="", help="Optional HTTPS or codexbuddy destination for Buddy")
    parser.add_argument("--caller-namespace-id", default=DEFAULT_NAMESPACE, help="Buddy callerNamespaceID")
    parser.add_argument("--notification-id", default="", help="Buddy notificationID; omit unless retrying")
    parser.add_argument("--timeout", type=int, default=30, help="Per-provider helper timeout in seconds")
    parser.add_argument("--config", default=None, help="Provider config TOML (default: example or user override)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mode = "check" if args.check else "send"
    notification = Notification(
        title=args.title,
        subtitle=args.subtitle,
        message=args.message,
        destination=args.destination,
        caller_namespace_id=args.caller_namespace_id,
        notification_id=args.notification_id,
        timeout=args.timeout,
    )
    try:
        providers = load_providers(resolve_config_path(args.config))
        results, status = run_fanout(mode, notification, providers)
    except (OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "notification_status": status,
                    "providers": [
                        {"provider": item.provider, "status": item.status, "detail": redact_detail(item.detail)}
                        for item in results
                    ],
                },
                indent=2,
            )
        )
    else:
        print(format_report(results, status))

    if mode == "check":
        return 0 if status == "checked" else 1
    return 0 if status in {"sent", "fallback sent", "indeterminate"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
