#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path
from typing import Any


MAX_IMAGE_BYTES = 25 * 1024 * 1024


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


def supported_image_content(data: bytes) -> bool:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if data.startswith(b"\xff\xd8\xff"):
        return True
    if data.startswith((b"GIF87a", b"GIF89a")):
        return True
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return True
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return True
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return data[8:12] in {
            b"avif",
            b"avis",
            b"heic",
            b"heix",
            b"hevc",
            b"hevx",
            b"mif1",
            b"msf1",
        }
    return False


def approved_image_roots(extra_roots: list[Path]) -> list[Path]:
    root_candidates = list(extra_roots)
    inbox_dir = os.environ.get("AI_INBOX_DIR")
    if inbox_dir:
        root_candidates.append(Path(inbox_dir))
    if not root_candidates:
        raise SystemExit("imagePaths requires AI_INBOX_DIR or --image-root")

    roots: list[Path] = []
    for root_candidate in root_candidates:
        try:
            root = root_candidate.expanduser().resolve(strict=True)
        except OSError as error:
            raise SystemExit("approved image root is unavailable") from error
        if not root.is_dir():
            raise SystemExit("approved image root must be a directory")
        if root not in roots:
            roots.append(root)
    return roots


def read_approved_image(
    image_path: str, image_index: int, image_roots: list[Path]
) -> bytes:
    label = f"imagePaths[{image_index}]"
    candidate = Path(image_path).expanduser()
    if not candidate.is_absolute():
        raise SystemExit(f"{label} must be an absolute path")
    if candidate.is_symlink():
        raise SystemExit(f"{label} must not be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise SystemExit(f"{label} is unavailable") from error
    if not any(resolved == root or root in resolved.parents for root in image_roots):
        raise SystemExit(f"{label} is outside approved image roots")

    descriptor = -1
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(resolved, flags)
        file_status = os.fstat(descriptor)
        if not stat.S_ISREG(file_status.st_mode):
            raise SystemExit(f"{label} must be a regular file")
        if file_status.st_size > MAX_IMAGE_BYTES:
            raise SystemExit(f"{label} exceeds the 25 MiB limit")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            data = handle.read(MAX_IMAGE_BYTES + 1)
    except SystemExit:
        raise
    except OSError as error:
        raise SystemExit(f"{label} could not be read safely") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    if len(data) > MAX_IMAGE_BYTES:
        raise SystemExit(f"{label} exceeds the 25 MiB limit")
    if not supported_image_content(data):
        raise SystemExit(f"{label} has unsupported image content")
    return data


def build_payload(
    spec: dict[str, Any], extra_image_roots: list[Path] | None = None
) -> dict[str, Any]:
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
    if image_paths:
        image_roots = approved_image_roots(extra_image_roots or [])
        for image_index, image_path in enumerate(image_paths):
            image_data = read_approved_image(image_path, image_index, image_roots)
            images.append(base64.b64encode(image_data).decode("ascii"))
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
    parser.add_argument(
        "--image-root",
        action="append",
        default=[],
        type=Path,
        help="Additional approved directory for imagePaths; may repeat.",
    )
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit("spec must be a JSON object")

    payload = build_payload(spec, args.image_root)
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
