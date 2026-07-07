---
name: mela-recipe-manager
description: Manage Pablo's Mela recipe library from Codex. Use for reading/searching/exporting Mela recipes with mela-cli, adding hand-authored recipes through the Mela macOS UI, creating .melarecipe artifacts, assigning categories, marking Want to Cook/Favorite, auditing duplicates, and verifying changes against the local synced Mela catalog.
---

# Mela Recipe Manager

Use this skill when Pablo asks to read, add, organize, audit, export, or manage recipes in Mela.

## Ground Rules

- Never write directly to `Curcuma.sqlite` or other Mela/Core Data/CloudKit files.
- Use `mela-cli` only for reads, search, stats, and export. It is read-only.
- Use Mela's own macOS UI for writes, then verify with `mela-cli`.
- Keep a `.spec.json` and `.melarecipe` artifact in `AI_INBOX_DIR` for every recipe created from chat/Craft/local notes.
- Treat Mela category changes as real library writes. Keep them narrow and verify.

## Setup

Preferred local command:

```bash
"$HOME/.local/bin/mela" doctor --format json
```

The wrapper points to a pinned venv with `mela-cli==1.0.1`. If missing, recreate it:

```bash
python3 -m venv "$HOME/.local/share/mela-cli-venv"
"$HOME/.local/share/mela-cli-venv/bin/python" -m pip install mela-cli==1.0.1
```

Then create `$HOME/.local/bin/mela` as a wrapper to the venv's `mela`.

## Read Workflow

Run a health check first:

```bash
mela doctor --format json
mela stats --format json
mela tags --format json
```

Search before acting:

```bash
mela search "recipe title" --format json
mela list --format json
mela show <pk-or-title> --format json
```

Export for backup or review:

```bash
mela export <pk-or-title> --format melarecipe --output "$AI_INBOX_DIR" --filename-style slug
```

Avoid `--filename-style id` for web-imported recipes because some IDs contain slashes.

## Add Workflow

1. Search Mela for likely duplicates by title and source.
2. Inspect existing categories with `mela tags --format json`.
3. Create or choose the recipe image before generating the import artifact when Pablo wants a picture. Image-gen images are acceptable. Save the final bitmap to `AI_INBOX_DIR` or another durable local path and reference it with an absolute path in `imagePaths`.
4. Create a recipe spec JSON with:
   - `title`
   - `summary` or `text`
   - `ingredients` as a list of strings
   - `instructions` as a list of strings
   - optional `notes`
   - optional `categories` or `tags`
   - optional `imagePaths` for local images to embed as base64 in `.melarecipe`; use this whenever Pablo wants an image from the start
   - optional `wantToCook` / `favorite`

Example image-first spec shape:

```json
{
  "title": "Cinnamon Vanilla Vegan Ninja Creami Ice Cream",
  "summary": "Creamy oat-cashew cinnamon vanilla pint for the Ninja Creami.",
  "ingredients": ["1 cup oat milk", "1/2 cup raw cashews, soaked"],
  "instructions": ["Blend the base until smooth.", "Freeze 24 hours, then spin."],
  "categories": ["Desserts"],
  "wantToCook": true,
  "imagePaths": ["/absolute/path/to/generated-cover.png"]
}
```

5. Generate the import artifact:

```bash
SKILL_DIR="$HOME/.agents/skills/productivity/mela-recipe-manager"
"$SKILL_DIR/scripts/recipe_to_melarecipe.py" "$SPEC_JSON" -o "$AI_INBOX_DIR"
```

6. If the spec includes `imagePaths` or `images`, import the generated `.melarecipe` through Mela's own import UI so the image is attached from the start. Do not use `add_recipe_to_mela.py` for image recipes; that helper fills the New Recipe editor and does not attach images.

Recommended verification before import:

```bash
python3 - <<'PY' "$MELARECIPE_FILE"
import base64, json, sys
p = sys.argv[1]
j = json.load(open(p))
images = j.get("images", [])
print({"images": len(images), "first_png": bool(images and base64.b64decode(images[0])[:8] == b"\x89PNG\r\n\x1a\n")})
PY
```

After importing, verify with `mela search` / `mela show` and confirm the saved recipe has `imageCount > 0`.

7. If the spec has no image, adding through the editor helper is acceptable:

```bash
"$SKILL_DIR/scripts/add_recipe_to_mela.py" "$SPEC_JSON"
```

The write helper uses Mela's `File > New Recipe`, fills the editor, saves, applies existing categories through `Recipe > Categories`, toggles Want to Cook/Favorite when requested, and prints the verified `mela search` result.

## Organization Rules

- Prefer existing broad categories over creating narrow one-off categories.
- Current observed categories include: `entrees`, `Desserts`, `breakfast`, `pasta`, `asian`, `bread`, `Cookies`, `protein`, `tacos`, `bases`, `Cakes`, `sauces`, `Sides`, `Dressing`, `drinks`, `soup`, `mexican`, `sandwiches`, `Smoothie`.
- Avoid using or expanding typo categories such as `sandwhiches`.
- For vegan desserts, default to `Desserts`; add narrower categories only when they already exist or Pablo asks for them.
- For recipes Pablo wants to try, use Want to Cook instead of inventing a category.

## Known Limits

- Mela imports `.melarecipe`/`.melarecipes`, but plain `open` did not reliably save a generated recipe during validation. Use the UI helper unless this is revalidated.
- Mela's public import field is `categories`; `mela-cli` exposes the same concept as `tags`. The artifact generator writes both for compatibility.
- Mela's public import format supports `images` as base64 strings. Prefer `imagePaths` in the local spec so the generator embeds image bytes into the `.melarecipe` artifact.
- The UI helper currently persists core recipe fields plus existing category menu choices and Want to Cook/Favorite. Source, servings, prep/cook/total time fields were not reliable via accessibility in the validated path; include important metadata in notes until that is improved.
- Always verify final state with `mela show <pk> --format json` before reporting success.
