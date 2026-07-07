#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "recipe"


def multiline(value: Any, field: str) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "\n".join(item.strip() for item in value if item.strip())
    raise SystemExit(f"{field} must be a string or list of strings")


def string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        seen: set[str] = set()
        result: list[str] = []
        for item in value:
            cleaned = item.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result
    raise SystemExit(f"{field} must be a list of strings")


def optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise SystemExit(f"{key} must be a string")
    value = value.strip()
    return value or None


def build_payload(spec: dict[str, Any]) -> dict[str, Any]:
    title = optional_string(spec, "title")
    if not title:
        raise SystemExit("title is required")

    ingredients = multiline(spec.get("ingredients"), "ingredients")
    instructions = multiline(spec.get("instructions"), "instructions")
    if not ingredients:
        raise SystemExit("ingredients are required")
    if not instructions:
        raise SystemExit("instructions are required")

    source_url = optional_string(spec, "sourceURL") or optional_string(spec, "link")
    source = optional_string(spec, "source")
    identifier_seed = source_url or f"codex.local/recipes/{slugify(title)}"
    identifier = optional_string(spec, "id") or str(uuid.uuid5(uuid.NAMESPACE_URL, identifier_seed))

    payload: dict[str, Any] = {
        "id": identifier,
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
        "favorite": bool(spec.get("favorite", False)),
        "wantToCook": bool(spec.get("wantToCook", False)),
    }

    for spec_key, mela_key in (
        ("text", "text"),
        ("summary", "text"),
        ("notes", "notes"),
        ("nutrition", "nutrition"),
        ("prepTime", "prepTime"),
        ("cookTime", "cookTime"),
        ("totalTime", "totalTime"),
        ("yield", "yield"),
        ("servings", "yield"),
    ):
        value = optional_string(spec, spec_key)
        if value and mela_key not in payload:
            payload[mela_key] = value

    if source_url:
        payload["link"] = source_url
    elif source:
        payload["link"] = source

    categories = string_list(spec.get("categories", spec.get("tags")), "categories")
    if categories:
        # Mela's public import docs call these categories. mela-cli exposes the
        # same concept as tags on read/export, so keep both for compatibility.
        payload["categories"] = categories
        payload["tags"] = categories

    images = string_list(spec.get("images"), "images")
    image_paths = string_list(spec.get("imagePaths"), "imagePaths")
    for image_path in image_paths:
        path = Path(image_path).expanduser()
        if not path.exists():
            raise SystemExit(f"image path does not exist: {path}")
        images.append(base64.b64encode(path.read_bytes()).decode("ascii"))
    if images:
        payload["images"] = images

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an importable .melarecipe JSON file from a structured recipe spec."
    )
    parser.add_argument("spec", type=Path, help="Recipe spec JSON file.")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("."), help="Destination directory.")
    parser.add_argument("--filename", help="Override output filename.")
    parser.add_argument("--compact", action="store_true", help="Write compact JSON.")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit("spec must be a JSON object")

    payload = build_payload(spec)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or f"{slugify(payload['title'])}.melarecipe"
    if not filename.endswith(".melarecipe"):
        filename += ".melarecipe"
    output_path = args.output_dir / filename

    if args.compact:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path.write_text(text + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
