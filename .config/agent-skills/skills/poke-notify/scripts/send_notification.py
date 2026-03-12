#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://poke.com/api/v1/inbound-sms/webhook"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or send a notification message through Poke's inbound SMS webhook."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Validate env and payload without sending anything.",
    )
    mode.add_argument(
        "--send",
        action="store_true",
        help="Send the validated payload to the webhook.",
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Message text to include in the minimal payload.",
    )
    return parser.parse_args()


def validate_env() -> str:
    api_key = os.environ.get("POKE_API_KEY", "")
    if not api_key:
        raise SystemExit("POKE_API_KEY is not set in the environment.")
    return api_key


def build_payload(message: str) -> bytes:
    payload = {"message": message}
    if not isinstance(payload["message"], str) or not payload["message"].strip():
        raise SystemExit("message must be a non-empty string.")
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def dry_run(payload: bytes) -> None:
    print(f"Endpoint: {ENDPOINT}")
    print("Authorization: Bearer $POKE_API_KEY")
    print(f"Payload: {payload.decode('utf-8')}")


def send(api_key: str, payload: bytes) -> None:
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"HTTP {response.status}")
            if body:
                print(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(f"HTTP {error.code}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        raise SystemExit(1) from error


def main() -> None:
    args = parse_args()
    api_key = validate_env()
    payload = build_payload(args.message)
    if args.check:
        dry_run(payload)
        return
    send(api_key, payload)


if __name__ == "__main__":
    main()
