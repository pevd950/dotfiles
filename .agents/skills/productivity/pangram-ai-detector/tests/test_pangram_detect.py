from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


HELPER_PATH = Path(__file__).parents[1] / "scripts" / "pangram_detect.py"
SPEC = importlib.util.spec_from_file_location("pangram_detect", HELPER_PATH)
assert SPEC is not None and SPEC.loader is not None
PANGRAM = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PANGRAM
SPEC.loader.exec_module(PANGRAM)

SOURCE_TEXT = "PRIVATE SOURCE TEXT THAT MUST NOT APPEAR"
SEGMENT_TEXT = "PRIVATE SEGMENT TEXT THAT MUST NOT APPEAR"


class FakeResponse:
    def __init__(self, payload: object):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class RawResponse(FakeResponse):
    def __init__(self, payload: bytes):
        self.payload = payload


def success_result(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "stage": "STAGE_SUCCESS",
        "text": SOURCE_TEXT,
        "version": "3.0",
        "headline": "AI Detected",
        "prediction": "Detector explanation",
        "prediction_short": "AI",
        "fraction_ai": 0.7,
        "fraction_ai_assisted": 0.2,
        "fraction_human": 0.1,
        "num_ai_segments": 1,
        "num_ai_assisted_segments": 0,
        "num_human_segments": 0,
        "windows": [
            {
                "text": SEGMENT_TEXT,
                "label": "AI-Generated",
                "ai_assistance_score": 0.85,
                "confidence": "High",
                "start_index": 0,
                "end_index": 20,
                "word_count": 4,
                "token_length": 5,
            }
        ],
    }
    result.update(overrides)
    return result


class PangramDetectTests(unittest.TestCase):
    def run_predict(self, responses: list[FakeResponse], **kwargs: object):
        with (
            mock.patch.dict(os.environ, {"PANGRAM_API_KEY": "test-only-key"}),
            mock.patch.object(
                PANGRAM.urllib.request, "urlopen", side_effect=responses
            ) as urlopen,
            mock.patch.object(PANGRAM.time, "sleep") as sleep,
        ):
            result = PANGRAM.predict(
                SOURCE_TEXT,
                timeout=3.0,
                poll_interval=float(kwargs.get("poll_interval", 0)),
                max_polls=int(kwargs.get("max_polls", 3)),
            )
        return result, urlopen, sleep

    def test_async_request_contract_and_polling(self) -> None:
        result, urlopen, sleep = self.run_predict(
            [
                FakeResponse({"task_id": "task/id"}),
                FakeResponse(
                    {"task_id": "task/id", "stage": "STAGE_PREPROCESSING"}
                ),
                FakeResponse(success_result()),
            ],
            poll_interval=0.25,
        )

        self.assertEqual(result["prediction_short"], "AI")
        self.assertEqual(urlopen.call_count, 3)
        create_request = urlopen.call_args_list[0].args[0]
        self.assertEqual(create_request.full_url, PANGRAM.CREATE_TASK_URL)
        self.assertEqual(create_request.get_method(), "POST")
        self.assertEqual(
            json.loads(create_request.data.decode("utf-8")),
            {"text": SOURCE_TEXT, "public_dashboard_link": False},
        )
        headers = {key.lower(): value for key, value in create_request.header_items()}
        self.assertEqual(headers["x-api-key"], "test-only-key")
        self.assertEqual(headers["content-type"], "application/json")

        first_poll = urlopen.call_args_list[1].args[0]
        self.assertEqual(
            first_poll.full_url, f"{PANGRAM.CREATE_TASK_URL}/task%2Fid"
        )
        self.assertEqual(first_poll.get_method(), "GET")
        sleep.assert_called_once_with(0.25)

    def test_success_result_is_cleaned_before_return(self) -> None:
        result, _, _ = self.run_predict(
            [FakeResponse({"task_id": "safe-task"}), FakeResponse(success_result())]
        )
        serialized = json.dumps(result)
        self.assertNotIn(SOURCE_TEXT, serialized)
        self.assertNotIn(SEGMENT_TEXT, serialized)
        self.assertNotIn('"text"', serialized)

    def test_json_and_summary_never_emit_source_text(self) -> None:
        result, _, _ = self.run_predict(
            [FakeResponse({"task_id": "safe-task"}), FakeResponse(success_result())]
        )
        sanitized = PANGRAM.sanitized_result(result, include_segments=True)
        output = io.StringIO()
        with redirect_stdout(output):
            print(json.dumps(sanitized))
            PANGRAM.print_summary(result, include_segments=True)
        rendered = output.getvalue()
        self.assertNotIn(SOURCE_TEXT, rendered)
        self.assertNotIn(SEGMENT_TEXT, rendered)
        self.assertIn("source text omitted", rendered)
        self.assertIn("Detector signal only", rendered)

    def test_provider_strings_cannot_echo_source_text(self) -> None:
        malicious = success_result(headline=SOURCE_TEXT, version=SOURCE_TEXT)
        malicious["windows"][0]["label"] = SOURCE_TEXT
        malicious["windows"][0]["confidence"] = "PRIVATE"
        result, _, _ = self.run_predict([
            FakeResponse({"task_id": "safe-task"}), FakeResponse(malicious)
        ])
        output = io.StringIO()
        with redirect_stdout(output):
            print(json.dumps(PANGRAM.sanitized_result(result, True)))
            PANGRAM.print_summary(result, True)
        self.assertNotIn(SOURCE_TEXT, output.getvalue())
        self.assertNotIn("PRIVATE", output.getvalue())
        self.assertEqual(result["version"], "unavailable")
        self.assertEqual(result["windows"][0]["label"], "Unknown")

    def test_predict_rejects_invalid_bounds_before_network_access(self) -> None:
        invalid_cases = [
            {"timeout": 0, "poll_interval": 0, "max_polls": 1},
            {"timeout": 1, "poll_interval": -1, "max_polls": 1},
            {"timeout": 1, "poll_interval": 0, "max_polls": 0},
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                with (
                    mock.patch.object(PANGRAM.urllib.request, "urlopen") as urlopen,
                    self.assertRaises(PANGRAM.PangramError),
                ):
                    PANGRAM.predict(SOURCE_TEXT, **case)
                urlopen.assert_not_called()

    def test_creation_requires_nonempty_task_id(self) -> None:
        with self.assertRaisesRegex(PANGRAM.PangramError, "task-creation"):
            self.run_predict([FakeResponse({})])

    def test_status_requires_stage(self) -> None:
        with self.assertRaisesRegex(PANGRAM.PangramError, "task status"):
            self.run_predict(
                [FakeResponse({"task_id": "safe-task"}), FakeResponse({})]
            )

    def test_status_rejects_mismatched_task_id(self) -> None:
        with self.assertRaisesRegex(PANGRAM.PangramError, "mismatched"):
            self.run_predict(
                [
                    FakeResponse({"task_id": "safe-task"}),
                    FakeResponse(
                        {"task_id": "different-task", "stage": "STAGE_PENDING"}
                    ),
                ]
            )

    def test_provider_failure_does_not_expose_remote_detail(self) -> None:
        failed = {
            "stage": "STAGE_FAILED",
            "headline": f"Provider echoed {SOURCE_TEXT}",
            "text": SOURCE_TEXT,
        }
        with self.assertRaises(PANGRAM.PangramError) as raised:
            self.run_predict(
                [FakeResponse({"task_id": "safe-task"}), FakeResponse(failed)]
            )
        self.assertNotIn(SOURCE_TEXT, str(raised.exception))
        self.assertEqual(
            str(raised.exception), "Pangram could not analyze the submitted text."
        )

    def test_poll_count_is_bounded(self) -> None:
        responses = [FakeResponse({"task_id": "safe-task"})] + [
            FakeResponse({"stage": "STAGE_PENDING"}) for _ in range(2)
        ]
        with self.assertRaisesRegex(PANGRAM.PangramError, "2 status checks"):
            self.run_predict(responses, max_polls=2)

    def test_success_requires_documented_fields(self) -> None:
        malformed = success_result()
        del malformed["headline"]
        with self.assertRaisesRegex(PANGRAM.PangramError, "headline"):
            self.run_predict(
                [FakeResponse({"task_id": "safe-task"}), FakeResponse(malformed)]
            )

    def test_fraction_rejects_bool_and_out_of_range(self) -> None:
        for invalid in (True, -0.1, 1.1, float("inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(PANGRAM.PangramError, "fraction_ai"):
                    self.run_predict(
                        [
                            FakeResponse({"task_id": "safe-task"}),
                            FakeResponse(success_result(fraction_ai=invalid)),
                        ]
                    )

    def test_window_text_must_exist_but_is_not_retained(self) -> None:
        malformed_window = success_result()
        malformed_window["windows"] = [
            {
                "label": "AI-Generated",
                "ai_assistance_score": 0.85,
                "confidence": "High",
                "start_index": 0,
                "end_index": 20,
                "word_count": 4,
                "token_length": 5,
            }
        ]
        with self.assertRaisesRegex(PANGRAM.PangramError, "window at index 0"):
            self.run_predict(
                [
                    FakeResponse({"task_id": "safe-task"}),
                    FakeResponse(malformed_window),
                ]
            )

    def test_http_error_body_is_never_read_or_exposed(self) -> None:
        error = urllib.error.HTTPError(
            PANGRAM.CREATE_TASK_URL,
            400,
            "bad request",
            {},
            io.BytesIO(f'{{"text": "{SOURCE_TEXT}"}}'.encode("utf-8")),
        )
        self.addCleanup(error.close)
        with (
            mock.patch.dict(os.environ, {"PANGRAM_API_KEY": "test-only-key"}),
            mock.patch.object(PANGRAM.urllib.request, "urlopen", side_effect=error),
            self.assertRaises(PANGRAM.PangramError) as raised,
        ):
            PANGRAM.predict(SOURCE_TEXT, timeout=3.0, max_polls=1)
        self.assertEqual(
            str(raised.exception),
            "Pangram returned HTTP 400 while creating the analysis task.",
        )
        self.assertNotIn(SOURCE_TEXT, str(raised.exception))

    def test_network_error_reason_is_not_exposed(self) -> None:
        error = urllib.error.URLError(f"network echoed {SOURCE_TEXT}")
        with (
            mock.patch.dict(os.environ, {"PANGRAM_API_KEY": "test-only-key"}),
            mock.patch.object(PANGRAM.urllib.request, "urlopen", side_effect=error),
            self.assertRaises(PANGRAM.PangramError) as raised,
        ):
            PANGRAM.predict(SOURCE_TEXT, timeout=3.0, max_polls=1)
        self.assertNotIn(SOURCE_TEXT, str(raised.exception))

    def test_non_json_response_is_safe(self) -> None:
        with self.assertRaisesRegex(PANGRAM.PangramError, "invalid JSON"):
            self.run_predict([RawResponse(SOURCE_TEXT.encode("utf-8"))])


if __name__ == "__main__":
    unittest.main()
