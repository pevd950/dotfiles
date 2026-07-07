#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import os
from pathlib import Path
from typing import Any


MELA = Path(os.environ.get("MELA_BIN", str(Path.home() / ".local/bin/mela"))).expanduser()


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=check, text=True, capture_output=True)


def osascript(script: str) -> None:
    run(["osascript", "-e", script])


def osa_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def multiline(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return ""


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("spec must be a JSON object")
    for key in ("title", "ingredients", "instructions"):
        if not data.get(key):
            raise SystemExit(f"{key} is required")
    return data


def mela_json(*args: str) -> Any:
    result = run([str(MELA), *args, "--format", "json"])
    return json.loads(result.stdout)


def existing_titles(title: str) -> list[dict[str, Any]]:
    return mela_json("search", title)


def existing_tags() -> set[str]:
    return {item["tag"] for item in mela_json("tags")}


def create_editor_record(spec: dict[str, Any]) -> None:
    title = str(spec["title"]).strip()
    description = str(spec.get("summary") or spec.get("text") or "").strip()
    ingredients = multiline(spec["ingredients"])
    instructions = multiline(spec["instructions"])
    notes = str(spec.get("notes") or "").strip()

    script = f'''
tell application "Mela" to activate
delay 0.5
tell application "System Events" to tell process "Mela"
  click menu item "New Recipe" of menu 1 of menu bar item "File" of menu bar 1
  delay 0.8
  set g to UI element 5 of UI element 1 of window 1
  set value of UI element 3 of g to {osa_quote(title)}
  set value of UI element 11 of g to {osa_quote(description)}
  set value of UI element 13 of g to {osa_quote(ingredients)}
  set value of UI element 15 of g to {osa_quote(instructions)}
  set value of UI element 17 of g to {osa_quote(notes)}
  click button "Save" of toolbar 1 of window 1
end tell
'''
    osascript(script)
    time.sleep(2)


def apply_menu_state(spec: dict[str, Any], available_tags: set[str]) -> list[str]:
    warnings: list[str] = []
    tags = spec.get("categories", spec.get("tags", [])) or []
    if isinstance(tags, str):
        tags = [tags]
    for tag in tags:
        tag = str(tag).strip()
        if not tag:
            continue
        if tag not in available_tags:
            warnings.append(f"category not applied because it does not exist in Mela: {tag}")
            continue
        script = f'''
tell application "Mela" to activate
delay 0.2
tell application "System Events" to tell process "Mela"
  click menu item {osa_quote(tag)} of menu 1 of menu item "Categories" of menu 1 of menu bar item "Recipe" of menu bar 1
end tell
'''
        osascript(script)
        time.sleep(0.3)

    if bool(spec.get("wantToCook", False)):
        osascript('''
tell application "Mela" to activate
delay 0.2
tell application "System Events" to tell process "Mela"
  click menu item "Want to Cook" of menu 1 of menu bar item "Recipe" of menu bar 1
end tell
''')
        time.sleep(0.3)

    if bool(spec.get("favorite", False)):
        osascript('''
tell application "Mela" to activate
delay 0.2
tell application "System Events" to tell process "Mela"
  click menu item "Favorite" of menu 1 of menu bar item "Recipe" of menu bar 1
end tell
''')
        time.sleep(0.3)

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add a recipe to Mela through the supported macOS UI and verify it with mela-cli."
    )
    parser.add_argument("spec", type=Path, help="Recipe spec JSON.")
    parser.add_argument("--allow-duplicate", action="store_true", help="Do not stop if the title already exists.")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    title = str(spec["title"]).strip()
    before = existing_titles(title)
    if before and not args.allow_duplicate:
        print(json.dumps({"status": "duplicate", "matches": before}, indent=2), file=sys.stderr)
        return 2

    tags = existing_tags()
    create_editor_record(spec)
    warnings = apply_menu_state(spec, tags)
    after = existing_titles(title)
    new_matches = [item for item in after if item not in before]
    if not new_matches and after:
        new_matches = after
    if not new_matches:
        print(json.dumps({"status": "not_found_after_save", "warnings": warnings}, indent=2), file=sys.stderr)
        return 3

    result = {"status": "ok", "matches": new_matches, "warnings": warnings}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
