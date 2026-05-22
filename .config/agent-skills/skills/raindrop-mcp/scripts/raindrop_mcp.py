#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.raindrop.io/rest/v2/ai/mcp"


def request(method, params=None):
    token = os.environ.get("RAINDROP_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "RAINDROP_ACCESS_TOKEN is not set. Source the host's local shell exports "
            "or set RAINDROP_ACCESS_TOKEN in the environment."
        )

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc

    data = json.loads(raw)
    if "error" in data:
        raise SystemExit(json.dumps(data["error"], indent=2, sort_keys=True))
    result = data.get("result", data)
    return unwrap_content_text(result)


def unwrap_content_text(result):
    content = result.get("content") if isinstance(result, dict) else None
    if not isinstance(content, list) or len(content) != 1:
        return result

    item = content[0]
    if not isinstance(item, dict) or item.get("type") != "text":
        return result

    text = item.get("text")
    if not isinstance(text, str):
        return result

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return result


def parse_json_arg(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON arguments: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description="Call the official Raindrop.io MCP endpoint.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("initialize", help="Run an MCP initialize probe.")
    sub.add_parser("tools", help="List available MCP tools.")
    call = sub.add_parser("call", help="Call a named MCP tool.")
    call.add_argument("tool")
    call.add_argument("arguments", nargs="?", help="JSON object of tool arguments.")
    args = parser.parse_args()

    if args.cmd == "initialize":
        result = request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "codex-raindrop-helper", "version": "1"},
            },
        )
    elif args.cmd == "tools":
        result = request("tools/list")
    else:
        result = request(
            "tools/call",
            {"name": args.tool, "arguments": parse_json_arg(args.arguments)},
        )

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
