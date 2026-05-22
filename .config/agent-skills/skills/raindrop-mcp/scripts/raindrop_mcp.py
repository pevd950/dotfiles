#!/usr/bin/env python3
import argparse
import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.raindrop.io/rest/v2/ai/mcp"
PROTOCOL_VERSION = "2025-11-25"


class RaindropMcpClient:
    def __init__(self):
        token = os.environ.get("RAINDROP_ACCESS_TOKEN")
        if not token or not token.strip():
            raise SystemExit(
                "RAINDROP_ACCESS_TOKEN is not set. Source the host's local shell exports "
                "or set RAINDROP_ACCESS_TOKEN in the environment."
            )
        self.token = token.strip()
        self.next_id = 1
        self.session_id = None
        self.protocol_version = PROTOCOL_VERSION

    def request(self, method, params=None, expect_response=True, retry_session_expired=True):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        request_id = None
        if expect_response:
            request_id = self.next_id
            payload["id"] = request_id
            self.next_id += 1

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": self.protocol_version,
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
            if (
                exc.code == 404
                and self.session_id
                and retry_session_expired
                and method not in {"initialize", "notifications/initialized"}
            ):
                self.session_id = None
                self.initialize()
                return self.request(
                    method,
                    params,
                    expect_response=expect_response,
                    retry_session_expired=False,
                )
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"Request failed: {exc.reason}") from exc

        if not expect_response:
            return None

        data = select_response(decode_response(raw), request_id)
        if "error" in data:
            raise SystemExit(json.dumps(data["error"], indent=2, sort_keys=True))
        result = data.get("result", data)
        result = unwrap_content_text(result)
        if isinstance(result, dict) and result.get("isError") is True:
            raise SystemExit(json.dumps(result, indent=2, sort_keys=True))
        return result

    def initialize(self):
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "codex-raindrop-helper", "version": "1"},
            },
        )
        if isinstance(result, dict) and isinstance(result.get("protocolVersion"), str):
            self.protocol_version = result["protocolVersion"]
        self.request("notifications/initialized", expect_response=False)
        return result


def decode_response(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    event_payloads = []
    event_data_lines = []
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = line[5:].strip()
            if data and data != "[DONE]":
                event_data_lines.append(data)
        elif not line and event_data_lines:
            event_payloads.append("\n".join(event_data_lines))
            event_data_lines = []
    if event_data_lines:
        event_payloads.append("\n".join(event_data_lines))

    parsed_payloads = []
    for data in event_payloads:
        try:
            parsed_payloads.append(json.loads(data))
        except json.JSONDecodeError:
            continue
    if len(parsed_payloads) == 1:
        return parsed_payloads[0]
    if parsed_payloads:
        return parsed_payloads

    raise SystemExit("Response was not valid JSON or JSON-bearing server-sent events.")


def select_response(data, request_id):
    if isinstance(data, dict):
        if data.get("id") != request_id:
            raise SystemExit("Response did not match the active JSON-RPC request id.")
        return data
    if not isinstance(data, list):
        raise SystemExit("Response was not a JSON-RPC object or batch.")
    for item in data:
        if isinstance(item, dict) and item.get("id") == request_id:
            return item
    raise SystemExit("Batched response did not contain the active JSON-RPC request id.")


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
