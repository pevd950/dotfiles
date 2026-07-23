from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "productivity"
    / "mela-recipe-manager"
    / "scripts"
    / "recipe_to_melarecipe.py"
)
MAX_IMAGE_BYTES = 25 * 1024 * 1024
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAusB9Y9Z4WQAAAAASUVORK5CYII="
)


class RecipeToMelaRecipeImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.inbox = self.root / "inbox"
        self.output = self.root / "output"
        self.inbox.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_helper(
        self,
        image_paths: list[Path],
        *,
        image_roots: list[Path] | None = None,
        include_inbox_env: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        spec_path = self.root / "recipe.spec.json"
        spec_path.write_text(
            json.dumps(
                {
                    "title": "Security Test Recipe",
                    "ingredients": ["one ingredient"],
                    "instructions": ["one instruction"],
                    "imagePaths": [str(path) for path in image_paths],
                }
            ),
            encoding="utf-8",
        )
        environment = {"PATH": os.environ.get("PATH", "")}
        if include_inbox_env:
            environment["AI_INBOX_DIR"] = str(self.inbox)
        command = [
            sys.executable,
            str(HELPER),
            str(spec_path),
            "-o",
            str(self.output),
        ]
        for image_root in image_roots or []:
            command.extend(["--image-root", str(image_root)])
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_allows_supported_image_inside_inbox(self) -> None:
        image_path = self.inbox / "cover.png"
        image_path.write_bytes(PNG_1X1)

        result = self.run_helper([image_path])

        self.assertEqual(result.returncode, 0, result.stderr)
        artifact = json.loads(
            (self.output / "security-test-recipe.melarecipe").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(base64.b64decode(artifact["images"][0]), PNG_1X1)

    def test_allows_supported_image_inside_explicit_root(self) -> None:
        approved_root = self.root / "approved"
        approved_root.mkdir()
        image_path = approved_root / "cover.png"
        image_path.write_bytes(PNG_1X1)

        result = self.run_helper(
            [image_path],
            image_roots=[approved_root],
            include_inbox_env=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_file_outside_approved_roots_without_leaking_path(self) -> None:
        unrelated_file = self.root / "unrelated.txt"
        unrelated_file.write_text("private-marker", encoding="utf-8")

        result = self.run_helper([unrelated_file])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside approved image roots", result.stderr)
        self.assertNotIn(str(unrelated_file), result.stderr)
        self.assertNotIn("private-marker", result.stderr)

    def test_rejects_symlink_even_when_target_is_inside_approved_root(self) -> None:
        image_path = self.inbox / "cover.png"
        image_path.write_bytes(PNG_1X1)
        symlink_path = self.inbox / "cover-link.png"
        symlink_path.symlink_to(image_path)

        result = self.run_helper([symlink_path])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not be a symlink", result.stderr)
        self.assertNotIn(str(symlink_path), result.stderr)

    def test_rejects_parent_symlink_that_escapes_approved_root(self) -> None:
        outside_root = self.root / "outside"
        outside_root.mkdir()
        image_path = outside_root / "cover.png"
        image_path.write_bytes(PNG_1X1)
        linked_directory = self.inbox / "linked-directory"
        linked_directory.symlink_to(outside_root, target_is_directory=True)

        result = self.run_helper([linked_directory / "cover.png"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside approved image roots", result.stderr)
        self.assertNotIn(str(image_path), result.stderr)

    def test_rejects_directory_inside_approved_root(self) -> None:
        directory_path = self.inbox / "not-a-file.png"
        directory_path.mkdir()

        result = self.run_helper([directory_path])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be a regular file", result.stderr)
        self.assertNotIn(str(directory_path), result.stderr)

    def test_rejects_non_image_file_inside_approved_root(self) -> None:
        non_image = self.inbox / "not-an-image.png"
        non_image.write_text("private-marker", encoding="utf-8")

        result = self.run_helper([non_image])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported image content", result.stderr)
        self.assertNotIn("private-marker", result.stderr)

    def test_rejects_oversized_image_before_embedding(self) -> None:
        oversized_image = self.inbox / "oversized.png"
        with oversized_image.open("wb") as handle:
            handle.write(PNG_1X1)
            handle.truncate(MAX_IMAGE_BYTES + 1)

        result = self.run_helper([oversized_image])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exceeds the 25 MiB limit", result.stderr)

    def test_requires_an_approved_root_for_image_paths(self) -> None:
        image_path = self.root / "cover.png"
        image_path.write_bytes(PNG_1X1)

        result = self.run_helper([image_path], include_inbox_env=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires AI_INBOX_DIR or --image-root", result.stderr)

    def test_recipe_without_image_paths_does_not_require_approved_root(self) -> None:
        result = self.run_helper([], include_inbox_env=False)

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
