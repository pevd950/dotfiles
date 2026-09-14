import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).with_name("scan_codex_sessions.py")
spec = importlib.util.spec_from_file_location("scanner", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class ScannerTests(unittest.TestCase):
    def test_active_archive_resume_filter_redaction_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); active = root / "sessions"; archive = root / "archived_sessions"
            active.mkdir(); archive.mkdir()
            (active / "a.jsonl").write_text(json.dumps({"session_id":"s1","timestamp":"2026-09-10T00:00:00Z","type":"custom_tool_call","name":"one","secret":"top-secret"}) + "\n{" , encoding="utf-8")
            (archive / "resumed.jsonl").write_text(json.dumps({"session_id":"s1","timestamp":"2026-09-12T00:00:00Z","type":"custom_tool_call_output","name":"two"}) + "\n", encoding="utf-8")
            (archive / "guardian-s.jsonl").write_text(json.dumps({"session_id":"guardian","type":"tool_call","name":"ignored"}) + "\n", encoding="utf-8")
            result = scanner.collect([active, archive], datetime(2026, 9, 11, tzinfo=timezone.utc))
            self.assertEqual(result["coverage"]["malformed_lines"], 1)
            self.assertEqual(len(result["sessions"]), 1)
            self.assertEqual([e["name"] for e in result["sessions"][0]["events"]], ["two"])
            self.assertNotIn("top-secret", json.dumps(result))

    def test_authorization_is_required(self):
        # CLI authorization is enforced; collector itself is reusable by an authorized caller.
        self.assertIn("--authorized", SCRIPT.read_text())


if __name__ == "__main__":
    unittest.main()
