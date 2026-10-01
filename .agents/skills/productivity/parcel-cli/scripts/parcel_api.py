#!/usr/bin/env python3
"""Small Parcel API helper for agent-safe local use."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE = "https://api.parcel.app/external"
STATUS = {
    0: "completed",
    1: "frozen",
    2: "in transit",
    3: "ready for pickup",
    4: "out for delivery",
    5: "not found",
    6: "failed delivery attempt",
    7: "exception",
    8: "info received",
}


def api_key() -> str:
    key = os.environ.get("PARCEL_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "PARCEL_API_KEY is not set. Source ~/.zshenv.local or set it in the environment."
        )
    return key


def request_json(
    method: str,
    path_or_url: str,
    *,
    data: dict[str, Any] | None = None,
    auth: bool = True,
) -> Any:
    url = path_or_url if path_or_url.startswith("http") else f"{API_BASE}{path_or_url}"
    body = None
    headers = {"Accept": "application/json"}
    if auth:
        headers["api-key"] = api_key()
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        # Provider details may echo private carrier inputs; expose only status.
        raise SystemExit(f"Parcel returned HTTP {exc.code}; check carrier inputs and quota.") from exc
    except urllib.error.URLError as exc:
        raise SystemExit("Parcel request failed; verify delivery state before retrying an add.") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit("Parcel returned a non-JSON response; verify delivery state before retrying an add.") from exc

    if isinstance(payload, dict) and payload.get("success") is False:
        raise SystemExit("Parcel API request failed; check carrier inputs and quota.")
    return payload


def load_carriers() -> dict[str, Any]:
    return request_json(
        "GET",
        "https://api.parcel.app/external/supported_carriers.json",
        auth=False,
    )


def command_carriers(args: argparse.Namespace) -> None:
    carriers = load_carriers()
    query = (args.query or "").lower()
    matches: dict[str, str] = {}
    for code, carrier in carriers.items():
        # Parcel's carrier catalog currently returns objects, although older
        # responses used plain strings.
        name = carrier.get("name", code) if isinstance(carrier, dict) else carrier
        if not isinstance(name, str):
            continue
        if not query or query in code.lower() or query in name.lower():
            matches[code] = name
    if args.json:
        print(json.dumps(matches, indent=2, sort_keys=True))
        return
    for code, name in sorted(matches.items(), key=lambda item: item[1].lower()):
        print(f"{code}\t{name}")


def fetch_deliveries(mode: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"filter_mode": mode})
    payload = request_json("GET", f"/deliveries/?{query}")
    return payload.get("deliveries", [])


def command_deliveries(args: argparse.Namespace) -> None:
    deliveries = fetch_deliveries(args.mode)
    if args.limit is not None:
        deliveries = deliveries[: args.limit]
    if args.json:
        print(json.dumps(deliveries, indent=2, sort_keys=True))
        return
    print(f"{len(deliveries)} {args.mode} deliveries")
    if args.summary:
        for item in deliveries:
            status = STATUS.get(item.get("status_code"), f"status {item.get('status_code')}")
            expected = item.get("date_expected") or item.get("timestamp_expected") or ""
            suffix = f" expected={expected}" if expected else ""
            print(
                f"- {item.get('description')} [{item.get('carrier_code')}] "
                f"{item.get('tracking_number')} - {status}{suffix}"
            )


def duplicate_exists(tracking: str) -> bool:
    needle = tracking.strip().lower()
    for mode in ("active", "recent"):
        for item in fetch_deliveries(mode):
            if str(item.get("tracking_number", "")).strip().lower() == needle:
                return True
    return False


def load_carrier_inputs(source: str | None) -> dict[str, str]:
    """Read private carrier fields without putting their values in argv or errors."""
    if source is None:
        return {}
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).expanduser().read_text(encoding="utf-8")
        fields = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit("Could not read carrier inputs as UTF-8 JSON.") from exc
    if not isinstance(fields, dict) or set(fields) - {"postcode", "email"}:
        raise SystemExit("Carrier inputs must be a JSON object containing only postcode and email.")
    if any(not isinstance(value, str) or not value.strip() for value in fields.values()):
        raise SystemExit("Carrier inputs must contain nonempty strings.")
    return {key: value.strip() for key, value in fields.items()}


def command_add(args: argparse.Namespace) -> None:
    payload = {
        "tracking_number": args.tracking.strip(),
        "carrier_code": args.carrier.strip(),
        "description": args.description.strip(),
        "language": args.language,
        "send_push_confirmation": bool(args.notify),
    }
    carrier_inputs = load_carrier_inputs(args.carrier_inputs_file)
    payload.update(carrier_inputs)
    if not args.no_duplicate_check and duplicate_exists(payload["tracking_number"]):
        print("Duplicate found in active/recent deliveries; no add attempted.")
        return

    if not args.confirm:
        print("Dry run. Add --confirm after explicit user approval to create this delivery.")
        preview = {key: value for key, value in payload.items() if key not in {"postcode", "email"}}
        if "postcode" in carrier_inputs:
            preview["postcode_supplied"] = True
        if "email" in carrier_inputs:
            preview["email_supplied"] = True
        print(json.dumps(preview, indent=2, sort_keys=True))
        return

    result = request_json("POST", "/add-delivery/", data=payload)
    print(json.dumps({"success": result.get("success") is True}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parcel API helper")
    sub = parser.add_subparsers(dest="command", required=True)

    carriers = sub.add_parser("carriers", help="Search supported carrier codes")
    carriers.add_argument("query", nargs="?", help="Carrier code or name filter")
    carriers.add_argument("--json", action="store_true", help="Print JSON")
    carriers.set_defaults(func=command_carriers)

    deliveries = sub.add_parser("deliveries", help="List recent or active deliveries")
    deliveries.add_argument("--mode", choices=("active", "recent"), default="active")
    deliveries.add_argument("--summary", action="store_true", help="Print compact summary")
    deliveries.add_argument("--json", action="store_true", help="Print raw delivery JSON")
    deliveries.add_argument("--limit", type=int, help="Limit output count")
    deliveries.set_defaults(func=command_deliveries)

    add = sub.add_parser("add", help="Add a delivery, dry-run by default")
    add.add_argument("--tracking", required=True, help="Tracking number")
    add.add_argument("--carrier", required=True, help="Parcel carrier code")
    add.add_argument("--description", required=True, help="Delivery description")
    add.add_argument("--language", default="en", help="ISO 639-1 language code")
    add.add_argument("--carrier-inputs-file", help="Private UTF-8 JSON file with postcode/email; use - to read stdin")
    add.add_argument("--notify", action="store_true", help="Send push confirmation")
    add.add_argument("--confirm", action="store_true", help="Actually add the delivery")
    add.add_argument(
        "--no-duplicate-check",
        action="store_true",
        help="Skip active/recent duplicate check before confirmed add or dry-run",
    )
    add.set_defaults(func=command_add)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
