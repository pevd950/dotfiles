#!/usr/bin/env python3
"""Convert Matter API item ids into Matter iOS universal links."""

from __future__ import annotations

import argparse
import sys


ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def decode_item_id(item_id: str) -> int:
    if not item_id.startswith("itm_"):
        raise ValueError(f"expected Matter item id starting with 'itm_', got {item_id!r}")

    suffix = item_id[4:]
    if not suffix:
        raise ValueError("Matter item id is missing its base62 suffix")

    value = 0
    for char in suffix:
        digit = ALPHABET.find(char)
        if digit < 0:
            raise ValueError(f"invalid base62 character {char!r} in {item_id!r}")
        value = value * 62 + digit
    return value


def app_link(item_id: str) -> str:
    return f"https://www.getmatter.com/d/entry/{decode_item_id(item_id)}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item_ids", nargs="+", help="Matter item ids like itm_8J1dX")
    parser.add_argument("--content-id-only", action="store_true", help="print only the decoded numeric id")
    args = parser.parse_args()

    for item_id in args.item_ids:
        try:
            content_id = decode_item_id(item_id)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2

        if args.content_id_only:
            print(content_id)
        else:
            print(f"{item_id}\t{content_id}\t{app_link(item_id)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
