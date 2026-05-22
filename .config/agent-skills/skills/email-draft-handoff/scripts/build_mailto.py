#!/usr/bin/env python3
import argparse
from pathlib import Path
from urllib.parse import quote


def read_body(args):
    if args.body_file:
        return Path(args.body_file).read_text()
    return args.body or ""


def main():
    parser = argparse.ArgumentParser(description="Build a URL-encoded mailto link.")
    parser.add_argument("--to", required=True, help="Recipient email address or comma-separated addresses.")
    parser.add_argument("--subject", default="", help="Email subject.")
    parser.add_argument("--body", default="", help="Email body text.")
    parser.add_argument("--body-file", help="Path to a UTF-8 text file containing the email body.")
    args = parser.parse_args()

    body = read_body(args)
    params = []
    if args.subject:
        params.append("subject=" + quote(args.subject))
    if body:
        params.append("body=" + quote(body))

    url = "mailto:" + quote(args.to, safe="@,")
    if params:
        url += "?" + "&".join(params)
    print(url)


if __name__ == "__main__":
    main()
