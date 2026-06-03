#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import math
import sys
import urllib.error
import urllib.parse
import urllib.request


MAX_TIMEOUT_SECONDS = 300.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Call the Craft API using local env auth.")
    parser.add_argument("method", choices=["GET", "POST", "PUT", "DELETE"])
    parser.add_argument("path", help="API path, such as /documents or /blocks")
    parser.add_argument("--query", action="append", default=[], help="Query pair key=value; may repeat")
    parser.add_argument("--json", dest="json_body", help="Inline JSON request body")
    parser.add_argument("--json-file", help="File containing JSON request body")
    parser.add_argument("--body-file", help="File containing a raw request body, for example upload bytes")
    parser.add_argument("--accept", default="application/json")
    parser.add_argument("--content-type", help="Content-Type for --body-file or an explicit JSON override")
    parser.add_argument("--auth", choices=["bearer", "x-craft-api-key"], default="bearer")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.timeout > MAX_TIMEOUT_SECONDS:
        print(f"--timeout must be a positive finite number <= {MAX_TIMEOUT_SECONDS:g}", file=sys.stderr)
        return 2

    base_url = os.environ.get("CRAFT_API_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("CRAFT_API_KEY", "")
    if not base_url or not api_key:
        print("CRAFT_API_BASE_URL and CRAFT_API_KEY must be set", file=sys.stderr)
        return 2
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in api_key):
        print("CRAFT_API_KEY contains invalid control characters", file=sys.stderr)
        return 2
    parsed_base_url = urllib.parse.urlsplit(base_url)
    if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
        print("CRAFT_API_BASE_URL must be an absolute http(s) URL", file=sys.stderr)
        return 2

    path = args.path if args.path.startswith("/") else f"/{args.path}"
    query_pairs = []
    for item in args.query:
        if "=" not in item:
            print(f"--query must be key=value: {item}", file=sys.stderr)
            return 2
        key, value = item.split("=", 1)
        query_pairs.append((key, value))
    query = urllib.parse.urlencode(query_pairs, doseq=True)
    url = f"{base_url}{path}"
    if query:
        separator = "&" if urllib.parse.urlsplit(url).query else "?"
        url = f"{url}{separator}{query}"

    body = None
    body_sources = [bool(args.json_body), bool(args.json_file), bool(args.body_file)]
    if sum(body_sources) > 1:
        print("Use only one of --json, --json-file, or --body-file", file=sys.stderr)
        return 2
    if args.json_body:
        try:
            body = json.dumps(json.loads(args.json_body)).encode("utf-8")
        except json.JSONDecodeError as error:
            print(f"Invalid JSON for --json: {error}", file=sys.stderr)
            return 2
    elif args.json_file:
        try:
            with open(args.json_file, "rb") as handle:
                raw_body = handle.read()
            body = json.dumps(json.loads(raw_body)).encode("utf-8")
        except OSError as error:
            print(f"Cannot read --json-file: {error}", file=sys.stderr)
            return 2
        except UnicodeDecodeError as error:
            print(f"Invalid UTF-8 in --json-file: {error}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as error:
            print(f"Invalid JSON in --json-file: {error}", file=sys.stderr)
            return 2
    elif args.body_file:
        try:
            with open(args.body_file, "rb") as handle:
                body = handle.read()
        except OSError as error:
            print(f"Cannot read --body-file: {error}", file=sys.stderr)
            return 2

    headers = {
        "Accept": args.accept,
        "User-Agent": "curl/8.7.1",
    }
    if body is not None:
        headers["Content-Type"] = args.content_type or "application/json"
    elif args.content_type:
        headers["Content-Type"] = args.content_type
    if args.auth == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        headers["x-craft-api-key"] = api_key

    request = urllib.request.Request(url, data=body, headers=headers, method=args.method)
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            payload = response.read()
            sys.stdout.buffer.write(payload)
            if sys.stdout.isatty() and not payload.endswith(b"\n"):
                sys.stdout.write("\n")
    except urllib.error.HTTPError as error:
        sys.stderr.write(f"Craft API returned HTTP {error.code}\n")
        detail = error.read().decode("utf-8", errors="replace")
        if detail:
            sys.stderr.write(detail[:2000] + "\n")
        return 1
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            sys.stderr.write(f"Craft API request timed out after {args.timeout:g}s\n")
            return 1
        sys.stderr.write(f"Craft API request failed: {error.reason}\n")
        return 1
    except TimeoutError:
        sys.stderr.write(f"Craft API request timed out after {args.timeout:g}s\n")
        return 1
    except (ValueError, http.client.InvalidURL) as error:
        sys.stderr.write(f"Craft API request is invalid: {error}\n")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
