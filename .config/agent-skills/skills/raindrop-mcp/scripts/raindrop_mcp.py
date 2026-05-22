#!/usr/bin/env python3
import argparse
import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.raindrop.io/rest/v2/ai/mcp"


class RaindropMcpClient:
    def __init__(self):
        self.token = os.environ.get("RAINDROP_ACCESS_TOKEN")
        if not self.token:
            raise SystemExit(
                "RAINDROP_ACCESS_TOKEN is not set. Source the host's local shell exports "
                "or set RAINDROP_ACCESS_TOKEN in the environment."
            )
        self.next_id = 1
        self.session_id = None

    def request(self, method, params=None):
        payload = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": method,
            "params": params or {},
        }
        self.next_id += 1

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                session_id = resp.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session_id = session_id
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"Request failed: {exc.reason}") from exc

        data = decode_response(raw)
        if "error" in data:
            raise SystemExit(json.dumps(data["error"], indent=2, sort_keys=True))
        result = data.get("result", data)
        return unwrap_content_text(result)

    def initialize(self):
        return self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "codex-raindrop-helper", "version": "1"},
            },
        )


def decode_response(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    data_lines = []
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = line.removeprefix("data:").strip()
            if data and data != "[DONE]":
                data_lines.append(data)

    for data in reversed(data_lines):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            continue

    raise SystemExit("Response was not valid JSON or JSON-bearing server-sent events.")


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
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return result
    if set(result.keys()) == {"content"}:
        return parsed
    unwrapped = dict(result)
    unwrapped["content"] = parsed
    return unwrapped


def parse_json_arg(raw):
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON arguments: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("Tool arguments must be a JSON object.")
    return parsed


def main():
    parser = argparse.ArgumentParser(description="Call the official Raindrop.io MCP endpoint.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("initialize", help="Run an MCP initialize probe.")
    sub.add_parser("tools", help="List available MCP tools.")
    call = sub.add_parser("call", help="Call a named MCP tool.")
    call.add_argument("tool")
    call.add_argument("arguments", nargs="?", help="JSON object of tool arguments.")
    args = parser.parse_args()

    client = RaindropMcpClient()
    if args.cmd == "initialize":
        result = client.initialize()
    elif args.cmd == "tools":
        client.initialize()
        result = client.request("tools/list")
    else:
        client.initialize()
        result = client.request(
            "tools/call",
            {"name": args.tool, "arguments": parse_json_arg(args.arguments)},
        )

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
