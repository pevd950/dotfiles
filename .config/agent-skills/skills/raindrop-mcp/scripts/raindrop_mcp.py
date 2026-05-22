#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.raindrop.io/rest/v2/ai/mcp"
PROTOCOL_VERSION = "2025-11-25"


class SessionExpired(Exception):
    pass


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
        self.last_event_id = None
        self.retry_delay_ms = None
        self.protocol_version = PROTOCOL_VERSION

    def reset_session(self):
        self.session_id = None
        self.last_event_id = None
        self.retry_delay_ms = None

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
                session_id = resp.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session_id = session_id
                response = self.read_response(resp, request_id)
        except urllib.error.HTTPError as exc:
            if (
                exc.code == 404
                and self.session_id
                and retry_session_expired
                and method != "initialize"
            ):
                self.reset_session()
                self.initialize(retry_session_expired=False)
                if method == "notifications/initialized":
                    return None
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

        try:
            data = select_response(decode_response(response), request_id)
        except SystemExit as exc:
            if self.session_id:
                try:
                    response = self.read_stream_response(request_id)
                except SessionExpired:
                    if retry_session_expired and method != "initialize":
                        self.reset_session()
                        self.initialize(retry_session_expired=False)
                        return self.request(
                            method,
                            params,
                            expect_response=expect_response,
                            retry_session_expired=False,
                        )
                    raise exc
                data = select_response(decode_response(response), request_id)
            else:
                raise exc
        if "error" in data:
            raise SystemExit(json.dumps(data["error"], indent=2, sort_keys=True))
        result = data.get("result", data)
        result = unwrap_content_text(result)
        if isinstance(result, dict) and result.get("isError") is True:
            raise SystemExit(json.dumps(result, indent=2, sort_keys=True))
        return result

    def initialize(self, retry_session_expired=True):
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "codex-raindrop-helper", "version": "1"},
            },
            retry_session_expired=retry_session_expired,
        )
        if isinstance(result, dict) and isinstance(result.get("protocolVersion"), str):
            self.protocol_version = result["protocolVersion"]
        self.request(
            "notifications/initialized",
            expect_response=False,
            retry_session_expired=retry_session_expired,
        )
        return result

    def read_response(self, resp, request_id):
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            return read_sse_events(resp, request_id, self)
        return resp.read().decode("utf-8", errors="replace")

    def read_stream_response(self, request_id):
        if self.retry_delay_ms is not None:
            time.sleep(self.retry_delay_ms / 1000)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "text/event-stream, application/json",
            "MCP-Protocol-Version": self.protocol_version,
            "Mcp-Session-Id": self.session_id,
        }
        if self.last_event_id:
            headers["Last-Event-ID"] = self.last_event_id
        req = urllib.request.Request(ENDPOINT, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return self.read_response(resp, request_id)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise SessionExpired from exc
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"HTTP {exc.code} while reading MCP stream: {detail}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"MCP stream read failed: {exc.reason}") from exc


def decode_response(raw):
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    event_payloads = []
    event_data_lines = []
    event_id = None
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = strip_sse_field_value(line[5:])
            if data != "[DONE]":
                event_data_lines.append(data)
        elif line.startswith("id:"):
            event_id = strip_sse_field_value(line[3:])
        elif not line:
            if event_id is not None or event_data_lines:
                event_payloads.append("\n".join(event_data_lines))
            event_data_lines = []
            event_id = None
    if event_id is not None or event_data_lines:
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


def strip_sse_field_value(value):
    if value.startswith(" "):
        return value[1:]
    return value


def read_sse_events(resp, request_id, client):
    parsed_payloads = []
    event_data_lines = []
    event_id = None
    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if line.startswith("id:"):
            event_id = strip_sse_field_value(line[3:])
            if event_id:
                client.last_event_id = event_id
        elif line.startswith("data:"):
            data = strip_sse_field_value(line[5:])
            if data != "[DONE]":
                event_data_lines.append(data)
        elif line.startswith("retry:"):
            retry = strip_sse_field_value(line[6:])
            if retry.isdigit():
                client.retry_delay_ms = int(retry)
        elif line == "":
            parsed = parse_sse_event(event_data_lines)
            if parsed is not None:
                parsed_payloads.append(parsed)
                try:
                    return select_response(parsed, request_id)
                except SystemExit:
                    pass
            event_data_lines = []
            event_id = None
    parsed = parse_sse_event(event_data_lines)
    if parsed is not None:
        parsed_payloads.append(parsed)
        try:
            return select_response(parsed, request_id)
        except SystemExit:
            pass
    return parsed_payloads


def parse_sse_event(event_data_lines):
    if not event_data_lines:
        return None
    payload = "\n".join(event_data_lines)
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def iter_response_objects(data):
    if isinstance(data, dict):
        yield data
    elif isinstance(data, list):
        for item in data:
            yield from iter_response_objects(item)


def select_response(data, request_id):
    if not isinstance(data, (dict, list)):
        raise SystemExit("Response was not a JSON-RPC object or batch.")
    for item in iter_response_objects(data):
        if item.get("id") == request_id:
            return item
    if isinstance(data, dict):
        raise SystemExit("Response did not match the active JSON-RPC request id.")
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
