#!/usr/bin/env python3
"""Regression tests for the notify-user fan-out CLI and adapters."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import send_notification as notify  # noqa: E402
from adapters import ProviderResult  # noqa: E402
from adapters import actionbuddy, codexbuddy, poke  # noqa: E402


SKILL_DIR = SCRIPTS.parent
EXAMPLE_CONFIG = SKILL_DIR / "config" / "providers.example.toml"
FANOUT = SCRIPTS / "send_notification.py"


def payload(**overrides):
    fields = dict(
        title="Codex",
        subtitle="Ready",
        message="For the user from Codex: PR is ready. Next step: review.",
    )
    fields.update(overrides)
    return notify.Notification(**fields)


def write_helper(directory: Path, name: str, script: str) -> Path:
    path = directory / name
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


class ConfigTests(unittest.TestCase):
    def test_example_config_orders_actionbuddy_then_codexbuddy_then_poke_all_enabled(self):
        providers = notify.load_providers(EXAMPLE_CONFIG)
        self.assertEqual([item.id for item in providers], ["actionbuddy", "codexbuddy", "poke"])
        self.assertTrue(providers[0].enabled)
        self.assertTrue(providers[1].enabled)
        self.assertTrue(providers[2].enabled)

    def test_load_providers_accepts_whitespace_in_table_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[ providers ]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            providers = notify.load_providers(path)
        self.assertEqual(providers[0].id, "poke")
        self.assertTrue(providers[0].enabled)

    def test_load_providers_rejects_unicode_whitespace_around_table_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "\u00a0[[providers]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"keys must appear under"):
                notify.load_providers(path)

    def test_load_providers_rejects_unicode_whitespace_in_table_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[\u00a0providers\u00a0]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"keys must appear under"):
                notify.load_providers(path)

    def test_load_providers_rejects_whitespace_inside_table_tokens(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[pro viders]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"keys must appear under"):
                notify.load_providers(path)

    def test_load_providers_rejects_unescaped_interior_quotes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "foo"bar"\n'
            )
            with self.assertRaisesRegex(notify.ValidationError, "invalid TOML scalar"):
                notify.load_providers(path)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                "id = 'actionbuddy'\n"
                "enabled = true\n"
                "helper = 'foo'bar'\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, "invalid TOML scalar"):
                notify.load_providers(path)

    def test_load_providers_rejects_bare_unquoted_scalar(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text("[[providers]]\nid = poke\nenabled = true\n")
            with self.assertRaisesRegex(notify.ValidationError, "invalid TOML scalar"):
                notify.load_providers(path)

    def test_load_providers_rejects_padded_provider_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = " poke "\n'
                "enabled = true\n"
            )
            with self.assertRaisesRegex(
                notify.ValidationError, "provider id must not have surrounding whitespace"
            ):
                notify.load_providers(path)

    def test_load_providers_rejects_duplicate_provider_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = true\n"
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"duplicate provider id 'poke'"):
                notify.load_providers(path)

    def test_load_providers_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = false\n"
                "enabled = true\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"duplicate key 'enabled'"):
                notify.load_providers(path)

    def test_load_providers_rejects_unknown_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "poke"\n'
                "enabeld = false\n"
            )
            with self.assertRaisesRegex(notify.ValidationError, r"unknown keys: enabeld"):
                notify.load_providers(path)

    def test_load_providers_reads_enable_flags_and_optional_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = false\n"
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = true\n"
                'helper = "/tmp/fake-poke.py"\n'
            )
            providers = notify.load_providers(path)
        self.assertEqual(providers[0].id, "actionbuddy")
        self.assertFalse(providers[0].enabled)
        self.assertTrue(providers[1].enabled)
        self.assertEqual(providers[1].helper, "/tmp/fake-poke.py")

    def test_load_providers_keeps_hash_inside_quoted_helper_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "/tmp/#notify/helper.py"  # local override\n'
            )
            providers = notify.load_providers(path)
        self.assertEqual(providers[0].helper, "/tmp/#notify/helper.py")

    def test_load_providers_honors_escaped_quotes_before_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "/tmp/foo\\"bar#baz.py"\n'
            )
            providers = notify.load_providers(path)
        self.assertEqual(providers[0].helper, '/tmp/foo"bar#baz.py')

    def test_unescape_toml_basic_supports_standard_escapes(self):
        self.assertEqual(notify._unescape_toml_basic(r"a\nb\tc"), "a\nb\tc")
        self.assertEqual(notify._unescape_toml_basic(r"x\u0023y"), "x#y")
        self.assertEqual(notify._unescape_toml_basic(r"\b\f"), "\b\f")

    def test_unescape_toml_basic_rejects_unknown_and_incomplete_escapes(self):
        with self.assertRaisesRegex(notify.ValidationError, r"invalid TOML escape: \\q"):
            notify._unescape_toml_basic(r"\q")
        with self.assertRaisesRegex(notify.ValidationError, "trailing backslash"):
            notify._unescape_toml_basic("foo\\")
        with self.assertRaisesRegex(notify.ValidationError, "invalid TOML unicode escape"):
            notify._unescape_toml_basic(r"\u12")

    def test_load_providers_rejects_unknown_toml_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "/tmp/foo\\qbar.py"\n'
            )
            with self.assertRaisesRegex(notify.ValidationError, r"invalid TOML escape: \\q"):
                notify.load_providers(path)

    def test_load_providers_rejects_incomplete_toml_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "foo\\"\n'
            )
            with self.assertRaisesRegex(notify.ValidationError, "trailing backslash"):
                notify.load_providers(path)

    def test_load_providers_decodes_unicode_escape_in_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.toml"
            path.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                'helper = "/tmp/foo\\u0023bar.py"\n'
            )
            providers = notify.load_providers(path)
        self.assertEqual(providers[0].helper, "/tmp/foo#bar.py")

    def test_poke_short_description_fits_openai_yaml_limit(self):
        yaml_path = SKILL_DIR.parent / "poke-notify" / "agents" / "openai.yaml"
        description = None
        for line in yaml_path.read_text().splitlines():
            if line.lstrip().startswith("short_description:"):
                description = line.split(":", 1)[1].strip().strip('"')
                break
        self.assertIsNotNone(description)
        self.assertGreaterEqual(len(description), 25)
        self.assertLessEqual(len(description), 64)

    def test_resolve_config_prefers_explicit_then_env_then_user_then_bundled(self):
        bundled = notify.bundled_config_path()
        self.assertEqual(bundled, EXAMPLE_CONFIG)
        with tempfile.TemporaryDirectory() as folder:
            explicit = Path(folder) / "explicit.toml"
            env_path = Path(folder) / "env.toml"
            explicit.write_text('[[providers]]\nid = "actionbuddy"\nenabled = true\n')
            env_path.write_text('[[providers]]\nid = "poke"\nenabled = true\n')
            self.assertEqual(notify.resolve_config_path(str(explicit)), explicit)
            with patch.dict(os.environ, {"NOTIFY_USER_CONFIG": str(env_path)}, clear=False):
                self.assertEqual(notify.resolve_config_path(None), env_path)
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": folder}, clear=False):
                env = {key: value for key, value in os.environ.items() if key != "NOTIFY_USER_CONFIG"}
                with patch.dict(os.environ, env, clear=True):
                    os.environ["XDG_CONFIG_HOME"] = folder
                    user = Path(folder) / "notify-user" / "providers.toml"
                    self.assertEqual(notify.resolve_config_path(None), bundled)
                    user.parent.mkdir()
                    user.write_text('[[providers]]\nid = "codexbuddy"\nenabled = true\n')
                    self.assertEqual(notify.resolve_config_path(None), user)


class PayloadTests(unittest.TestCase):
    def test_rejects_empty_message(self):
        with self.assertRaisesRegex(notify.ValidationError, "message"):
            notify.validate_notification(payload(message="  "))

    def test_poke_folds_title_and_subtitle_into_one_paragraph(self):
        folded = poke.fold_message(payload())
        self.assertIn("Codex", folded)
        self.assertIn("Ready", folded)
        self.assertIn("PR is ready", folded)
        self.assertNotIn("\n", folded)

    def test_codexbuddy_enforces_byte_limits_and_id_shape(self):
        with self.assertRaisesRegex(notify.ValidationError, "title"):
            codexbuddy.validate_fields(payload(title="n" * 121))
        with self.assertRaisesRegex(notify.ValidationError, "subtitle"):
            codexbuddy.validate_fields(payload(subtitle="s" * 161))
        with self.assertRaisesRegex(notify.ValidationError, "message"):
            codexbuddy.validate_fields(payload(message="b" * 561))
        with self.assertRaisesRegex(notify.ValidationError, "callerNamespaceID"):
            codexbuddy.validate_fields(payload(caller_namespace_id="bad id"))


class AdapterTests(unittest.TestCase):
    def test_actionbuddy_wraps_existing_helper_check_and_send(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "actionbuddy.py",
                "#!/usr/bin/env python3\n"
                "import json,sys\n"
                "mode='check' if '--check' in sys.argv else 'send'\n"
                "title = next(a.split('=',1)[1] for a in sys.argv if a.startswith('--title='))\n"
                "print(json.dumps({'mode': mode, 'title': title}))\n",
            )
            spec = notify.ProviderSpec(id="actionbuddy", enabled=True, helper=str(helper))
            checked = actionbuddy.run("check", payload(), spec)
            sent = actionbuddy.run("send", payload(), spec)
        self.assertEqual(checked.status, "checked")
        self.assertEqual(sent.status, "sent")
        self.assertIn("actionbuddy", checked.provider)

    def test_actionbuddy_forwards_configured_timeout_to_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "actionbuddy.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('OK: timeout=' + next(a.split('=',1)[1] for a in sys.argv if a.startswith('--timeout=')))\n",
            )
            spec = notify.ProviderSpec(id="actionbuddy", enabled=True, helper=str(helper))
            result = actionbuddy.run("check", payload(timeout=60), spec)
        self.assertEqual(result.status, "checked")
        self.assertEqual(result.detail, "helper ok")

    def test_actionbuddy_passes_option_like_fields_without_argparse_reinterpreting_them(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "actionbuddy.py",
                "#!/usr/bin/env python3\n"
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--check', action='store_true')\n"
                "p.add_argument('--send', action='store_true')\n"
                "p.add_argument('--title')\n"
                "p.add_argument('--subtitle')\n"
                "p.add_argument('--message', required=True)\n"
                "p.add_argument('--timeout', type=int, default=30)\n"
                "args = p.parse_args()\n"
                "print('OK: message=' + args.message)\n",
            )
            spec = notify.ProviderSpec(id="actionbuddy", enabled=True, helper=str(helper))
            result = actionbuddy.run(
                "check",
                payload(title="--title-like", subtitle="-ready", message="--blocked"),
                spec,
            )
        self.assertEqual(result.status, "checked")
        self.assertEqual(result.detail, "helper ok")

    def test_actionbuddy_outer_timeout_allows_both_shortcuts_probes(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(Path(folder), "actionbuddy.py", "#!/usr/bin/env python3\nprint('unused')\n")
            spec = notify.ProviderSpec(id="actionbuddy", enabled=True, helper=str(helper))
            captured: dict[str, object] = {}

            def fake_run(*args, **kwargs):
                captured["timeout"] = kwargs.get("timeout")
                return subprocess.CompletedProcess(args[0], 0, stdout="OK: sent\n", stderr="")

            with patch.object(actionbuddy.subprocess, "run", side_effect=fake_run):
                result = actionbuddy.run("send", payload(timeout=60), spec)
        self.assertEqual(result.status, "sent")
        self.assertEqual(captured["timeout"], 60 + actionbuddy.HELPER_OVERHEAD_SECONDS)

    def test_actionbuddy_failed_helper_does_not_report_raw_stderr(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "actionbuddy.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('Shortcut failed with exit 1: token leaked', file=sys.stderr)\n"
                "raise SystemExit(1)\n",
            )
            spec = notify.ProviderSpec(id="actionbuddy", enabled=True, helper=str(helper))
            result = actionbuddy.run("send", payload(), spec)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.detail, "helper failed (exit 1)")
        self.assertNotIn("token leaked", result.detail)

    def test_actionbuddy_missing_helper_is_failed_not_skipped(self):
        result = actionbuddy.run(
            "check",
            payload(),
            notify.ProviderSpec(id="actionbuddy", enabled=True, helper="/missing/actionbuddy.py"),
        )
        self.assertEqual(result.status, "failed")
        self.assertIn("helper not found", result.detail)

    def test_actionbuddy_classifies_absent_listed_shortcut_as_failed(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr="ERROR: Send Notification is not listed by shortcuts; wired",
        )
        self.assertEqual(result, "failed")

    def test_actionbuddy_absent_shortcut_is_failed_even_with_missing_db_marker(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr=(
                "ERROR: Send Notification is not listed by shortcuts; "
                "Shortcuts database not found: /missing/Shortcuts.sqlite"
            ),
        )
        self.assertEqual(result, "failed")

    def test_actionbuddy_classifies_missing_shortcuts_db_as_skip(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr="ERROR: Shortcuts database not found: /tmp/Shortcuts.sqlite",
        )
        self.assertEqual(result, "skipped")

    def test_actionbuddy_timeout_warning_is_indeterminate(self):
        result = actionbuddy.classify(
            returncode=0,
            stdout="",
            stderr="WARN: Shortcut timed out after 30s; delivery may have succeeded; wired",
        )
        self.assertEqual(result, "indeterminate")

    def test_actionbuddy_sqlite_tcc_error_is_not_failed(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr="ERROR: unable to open database file",
        )
        self.assertIn(result, {"skipped", "indeterminate"})

    def test_actionbuddy_sqlite_warning_with_successful_send_is_ok(self):
        result = actionbuddy.classify(
            returncode=0,
            stdout="OK: Notification sent!; sqlite wiring check skipped (Operation not permitted)",
            stderr="WARN: Shortcuts database unreadable; Send Notification listed by shortcuts",
        )
        self.assertEqual(result, "ok")

    def test_actionbuddy_shortcut_run_failure_is_failed_even_with_sqlite_warning(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr=(
                "ERROR: Shortcut failed with exit 1: no stderr; "
                "WARN: Shortcuts database unreadable; sqlite wiring check skipped "
                "(Operation not permitted)"
            ),
        )
        self.assertEqual(result, "failed")

    def test_actionbuddy_list_timeout_warning_is_indeterminate_even_with_missing_db(self):
        result = actionbuddy.classify(
            returncode=0,
            stdout="",
            stderr=(
                "WARN: shortcuts list timed out or failed; "
                "Shortcuts database not found: /tmp/Shortcuts.sqlite"
            ),
        )
        self.assertEqual(result, "indeterminate")

    def test_actionbuddy_timeout_is_indeterminate_even_with_missing_db_marker(self):
        result = actionbuddy.classify(
            returncode=0,
            stdout="",
            stderr=(
                "WARN: Shortcut timed out after 30s; delivery may have succeeded; "
                "Shortcuts database not found: /tmp/Shortcuts.sqlite"
            ),
        )
        self.assertEqual(result, "indeterminate")

    def test_actionbuddy_classifies_missing_shortcuts_binary_as_skip(self):
        result = actionbuddy.classify(
            returncode=1,
            stdout="",
            stderr=(
                "ERROR: shortcuts executable not found; ActionBuddy is unavailable; "
                "Shortcuts database not found: /missing/Shortcuts.sqlite"
            ),
        )
        self.assertEqual(result, "skipped")

    def test_poke_soft_skips_when_api_key_is_missing(self):
        with patch.dict(os.environ, {"POKE_API_KEY": ""}, clear=False):
            result = poke.run("check", payload(), notify.ProviderSpec("poke", True))
        self.assertEqual(result.status, "skipped")
        self.assertIn("POKE_API_KEY", result.detail)

    def test_poke_wraps_existing_helper_and_never_logs_api_key(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "poke.py",
                "#!/usr/bin/env python3\n"
                "import os,sys\n"
                "assert os.environ.get('POKE_API_KEY') == 'secret-key'\n"
                "print('Endpoint: https://poke.com/api/v1/inbound/api-message')\n"
                "print('Payload: {\"message\":\"folded\"}')\n",
            )
            spec = notify.ProviderSpec(id="poke", enabled=True, helper=str(helper))
            with patch.dict(os.environ, {"POKE_API_KEY": "secret-key"}):
                result = poke.run("check", payload(), spec)
        self.assertEqual(result.status, "checked")
        self.assertEqual(result.detail, "helper ok")
        self.assertNotIn("secret-key", result.detail)
        self.assertNotIn("folded", result.detail)

    def test_poke_passes_option_like_message_without_argparse_reinterpreting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "poke.py",
                "#!/usr/bin/env python3\n"
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('--check', action='store_true')\n"
                "p.add_argument('--send', action='store_true')\n"
                "p.add_argument('--message', required=True)\n"
                "args = p.parse_args()\n"
                "print('OK: message=' + args.message)\n",
            )
            spec = notify.ProviderSpec(id="poke", enabled=True, helper=str(helper))
            with patch.dict(os.environ, {"POKE_API_KEY": "secret-key"}):
                result = poke.run(
                    "check",
                    payload(title="", subtitle="", message="--blocked"),
                    spec,
                )
        self.assertEqual(result.status, "checked")
        self.assertEqual(result.detail, "helper ok")

    def test_poke_failed_helper_does_not_report_raw_stderr(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "poke.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('HTTP 401 {\"error\":\"token leaked\"}', file=sys.stderr)\n"
                "raise SystemExit(1)\n",
            )
            spec = notify.ProviderSpec(id="poke", enabled=True, helper=str(helper))
            with patch.dict(os.environ, {"POKE_API_KEY": "secret-key"}):
                result = poke.run("send", payload(), spec)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.detail, "helper failed (exit 1)")
        self.assertNotIn("token leaked", result.detail)

    def test_codexbuddy_soft_skips_when_host_unavailable(self):
        result = codexbuddy.run("check", payload(), notify.ProviderSpec("codexbuddy", True), host_probe=lambda: False)
        self.assertEqual(result.status, "skipped")
        self.assertIn("Host/MCP unavailable", result.detail)

    def test_codexbuddy_skips_unavailable_host_before_byte_limits(self):
        result = codexbuddy.run(
            "check",
            payload(message="b" * 561),
            notify.ProviderSpec("codexbuddy", True),
            host_probe=lambda: False,
        )
        self.assertEqual(result.status, "skipped")
        self.assertIn("Host/MCP unavailable", result.detail)

    def test_codexbuddy_does_not_invent_a_send_bypass_when_host_is_present(self):
        result = codexbuddy.run(
            "send",
            payload(caller_namespace_id="notify-user", notification_id="pr-78"),
            notify.ProviderSpec("codexbuddy", True),
            host_probe=lambda: True,
        )
        self.assertEqual(result.status, "skipped")
        self.assertIn("explicit user approval", result.detail.lower())
        self.assertNotIn("bypass", result.detail.lower())

    def test_codexbuddy_field_limit_skips_instead_of_failing_check(self):
        result = codexbuddy.run(
            "check",
            payload(message="b" * 561),
            notify.ProviderSpec("codexbuddy", True),
            host_probe=lambda: True,
        )
        self.assertEqual(result.status, "skipped")
        self.assertIn("560-byte", result.detail)


class FanoutTests(unittest.TestCase):
    def test_empty_runners_map_does_not_fall_back_to_global_runners(self):
        results, status = notify.run_fanout(
            "send",
            payload(),
            [notify.ProviderSpec("poke", True)],
            runners={},
        )
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(results[0].detail, "unknown provider id")
        self.assertEqual(status, "failed")

    def test_disabled_providers_are_not_called(self):
        calls = []

        def recording(mode, notification, spec, **_kwargs):
            calls.append(spec.id)
            return ProviderResult(spec.id, "sent", "ok")

        providers = [
            notify.ProviderSpec("actionbuddy", True),
            notify.ProviderSpec("codexbuddy", True),
            notify.ProviderSpec("poke", False),
        ]
        results, status = notify.run_fanout(
            "send",
            payload(),
            providers,
            runners={"actionbuddy": recording, "codexbuddy": recording, "poke": recording},
        )
        self.assertEqual(calls, ["actionbuddy", "codexbuddy"])
        self.assertEqual([item.status for item in results if item.provider == "poke"], ["disabled"])
        self.assertEqual(status, "sent")

    def test_no_silent_poke_fallback_when_poke_is_disabled_and_primary_fails(self):
        def fail_actionbuddy(mode, notification, spec, **_kwargs):
            return ProviderResult("actionbuddy", "failed", "shortcut error")

        def boom(mode, notification, spec, **_kwargs):
            raise AssertionError("poke must not run when disabled")

        results, status = notify.run_fanout(
            "send",
            payload(),
            [notify.ProviderSpec("actionbuddy", True), notify.ProviderSpec("poke", False)],
            runners={"actionbuddy": fail_actionbuddy, "poke": boom},
        )
        self.assertEqual(status, "failed")
        self.assertEqual(results[-1].status, "disabled")

    def test_fallback_sent_when_primary_fails_and_later_enabled_provider_sends(self):
        runners = {
            "actionbuddy": lambda mode, notification, spec, **_: ProviderResult("actionbuddy", "failed", "no shortcuts"),
            "codexbuddy": lambda mode, notification, spec, **_: ProviderResult("codexbuddy", "sent", "delivered"),
        }
        _results, status = notify.run_fanout(
            "send",
            payload(),
            [notify.ProviderSpec("actionbuddy", True), notify.ProviderSpec("codexbuddy", True)],
            runners=runners,
        )
        self.assertEqual(status, "fallback sent")

    def test_indeterminate_when_send_times_out_without_confirmed_delivery(self):
        _results, status = notify.run_fanout(
            "send",
            payload(),
            [notify.ProviderSpec("actionbuddy", True)],
            runners={
                "actionbuddy": lambda mode, notification, spec, **_: ProviderResult(
                    "actionbuddy", "indeterminate", "timeout"
                )
            },
        )
        self.assertEqual(status, "indeterminate")

    def test_skipped_hosts_do_not_fail_check(self):
        _results, status = notify.run_fanout(
            "check",
            payload(),
            [notify.ProviderSpec("actionbuddy", True), notify.ProviderSpec("codexbuddy", True)],
            runners={
                "actionbuddy": lambda mode, notification, spec, **_: ProviderResult(
                    "actionbuddy", "skipped", "Shortcuts database not found"
                ),
                "codexbuddy": lambda mode, notification, spec, **_: ProviderResult(
                    "codexbuddy", "skipped", "Host/MCP unavailable"
                ),
            },
        )
        self.assertEqual(status, "checked")

    def test_provider_exception_fails_that_provider_and_continues(self):
        def boom(mode, notification, spec, **_kwargs):
            raise OSError("unexpected adapter crash")

        results, status = notify.run_fanout(
            "check",
            payload(),
            [notify.ProviderSpec("actionbuddy", True), notify.ProviderSpec("codexbuddy", True)],
            runners={
                "actionbuddy": boom,
                "codexbuddy": lambda mode, notification, spec, **_: ProviderResult(
                    "codexbuddy", "skipped", "Host/MCP unavailable"
                ),
            },
        )
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(results[0].detail, "provider raised an unexpected error")
        self.assertEqual(results[1].status, "skipped")
        self.assertEqual(status, "failed")


class CliTests(unittest.TestCase):
    def test_check_cli_with_all_skipped_providers_exits_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "providers.toml"
            config.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                "[[providers]]\n"
                'id = "codexbuddy"\n'
                "enabled = true\n"
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = false\n"
            )
            helper = write_helper(
                Path(folder),
                "missing_db.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('ERROR: Shortcuts database not found: /missing', file=sys.stderr)\n"
                "sys.exit(1)\n",
            )
            config.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                f'helper = "{helper}"\n'
                "[[providers]]\n"
                'id = "codexbuddy"\n'
                "enabled = true\n"
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = false\n"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(FANOUT),
                    "--check",
                    "--config",
                    str(config),
                    "--title",
                    "Codex",
                    "--subtitle",
                    "Ready",
                    "--message",
                    "For the user from Codex: CLI check.",
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("actionbuddy: skipped", completed.stdout)
        self.assertRegex(completed.stdout, r"codexbuddy: (skipped|checked)")
        self.assertIn("poke: disabled", completed.stdout)
        self.assertIn("notification_status: checked", completed.stdout)

    def test_format_report_redacts_home_paths(self):
        home = str(Path.home())
        report = notify.format_report(
            [ProviderResult("actionbuddy", "failed", f"Shortcut failed: {home}/Library/Shortcuts/Shortcuts.sqlite")],
            "failed",
        )
        self.assertNotIn(home, report)
        self.assertIn("$HOME/Library/Shortcuts/Shortcuts.sqlite", report)

    def test_json_check_output_includes_per_provider_status(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "ok.py",
                "#!/usr/bin/env python3\nprint('OK: Send Notification is available')\n",
            )
            config = Path(folder) / "providers.toml"
            config.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                f'helper = "{helper}"\n'
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = false\n"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(FANOUT),
                    "--check",
                    "--json",
                    "--config",
                    str(config),
                    "--message",
                    "JSON check body",
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["notification_status"], "checked")
        providers = {item["provider"]: item["status"] for item in payload["providers"]}
        self.assertEqual(providers["actionbuddy"], "checked")
        self.assertEqual(providers["poke"], "disabled")


class AdapterPathTests(unittest.TestCase):
    def test_default_helpers_point_at_existing_provider_scripts(self):
        self.assertTrue(actionbuddy.default_helper().is_file())
        self.assertTrue(poke.default_helper().is_file())

    def test_bundled_example_check_soft_skips_unavailable_backends(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = write_helper(
                Path(folder),
                "actionbuddy.py",
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('ERROR: Shortcuts database not found: /missing', file=sys.stderr)\n"
                "sys.exit(1)\n",
            )
            config = Path(folder) / "providers.toml"
            config.write_text(
                "[[providers]]\n"
                'id = "actionbuddy"\n'
                "enabled = true\n"
                f'helper = "{helper}"\n'
                "[[providers]]\n"
                'id = "codexbuddy"\n'
                "enabled = true\n"
                "[[providers]]\n"
                'id = "poke"\n'
                "enabled = true\n"
            )
            env = {key: value for key, value in os.environ.items() if key != "POKE_API_KEY"}
            completed = subprocess.run(
                [
                    sys.executable,
                    str(FANOUT),
                    "--check",
                    "--config",
                    str(config),
                    "--title",
                    "Codex",
                    "--subtitle",
                    "Validation",
                    "--message",
                    "For the user from Codex: notify-user check on this host.",
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("actionbuddy: skipped", completed.stdout)
        self.assertRegex(completed.stdout, r"codexbuddy: (skipped|checked)")
        self.assertRegex(completed.stdout, r"poke: skipped")
        self.assertNotIn("poke: disabled", completed.stdout)
        self.assertIn("notification_status: checked", completed.stdout)


if __name__ == "__main__":
    unittest.main()
