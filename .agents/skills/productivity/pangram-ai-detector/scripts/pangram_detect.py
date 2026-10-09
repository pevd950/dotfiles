#!/usr/bin/env python3
"""Analyze requested text with Pangram's asynchronous AI-detection API."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_ROOT = "https://text.external-api.pangram.com"
CREATE_TASK_URL = f"{API_ROOT}/task"
DEFAULT_TIMEOUT = 60.0
DEFAULT_POLL_INTERVAL = 1.0
DEFAULT_MAX_POLLS = 60
TERMINAL_SUCCESS = "STAGE_SUCCESS"
TERMINAL_FAILURE = "STAGE_FAILED"
KNOWN_CLASSIFICATIONS = {"AI", "AI-Assisted", "Human", "Mixed"}


class PangramError(RuntimeError):
    """A safe, user-facing Pangram client error."""


def api_key() -> str:
    key = os.environ.get("PANGRAM_API_KEY", "").strip()
    if not key:
        raise PangramError(
            "PANGRAM_API_KEY is not set. Source ~/.zshenv.local or set it in the environment."
        )
    return key


def load_text(args: argparse.Namespace) -> str:
    sources = sum((args.text is not None, args.file is not None))
    if sources > 1:
        raise SystemExit("Use only one of --text or --file.")

    if args.text is not None:
        text = args.text
    elif args.file is not None:
        try:
            text = Path(args.file).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Could not read input file: {args.file}") from exc
        except UnicodeError as exc:
            raise SystemExit(f"Input file is not valid UTF-8: {args.file}") from exc
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        raise SystemExit("Provide --text, --file, or pipe text on stdin.")

    text = text.strip()
    if not text:
        raise SystemExit("The submitted text is empty.")
    return text


def _request_json(
    request: urllib.request.Request, timeout: float, operation: str
) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        # Do not read or expose the provider response body: it may contain source text.
        raise PangramError(
            f"Pangram returned HTTP {exc.code} while {operation}."
        ) from exc
    except urllib.error.URLError as exc:
        # URL error reasons can contain provider-controlled or environment-sensitive text.
        raise PangramError(f"Pangram could not be reached while {operation}.") from exc
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        raise PangramError(f"Pangram did not respond while {operation}.") from exc

    try:
        decoded = raw.decode("utf-8")
        result = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PangramError(
            f"Pangram returned an invalid JSON response while {operation}."
        ) from exc
    if not isinstance(result, dict):
        raise PangramError(
            f"Pangram returned an unexpected response shape while {operation}."
        )
    return result


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": api_key(),
    }


def _required_string(
    result: dict[str, Any], key: str, *, max_length: int | None = None
) -> str:
    value = result.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PangramError(f"Pangram's completed result has an invalid '{key}' field.")
    value = value.strip()
    if max_length is not None and len(value) > max_length:
        raise PangramError(f"Pangram's completed result has an invalid '{key}' field.")
    return value


def _required_fraction(result: dict[str, Any], key: str) -> float:
    value = result.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PangramError(f"Pangram's completed result has an invalid '{key}' field.")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise PangramError(f"Pangram's completed result has an invalid '{key}' field.")
    return numeric


def _required_count(result: dict[str, Any], key: str) -> int:
    value = result.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PangramError(f"Pangram's completed result has an invalid '{key}' field.")
    return value


def _clean_windows(result: dict[str, Any]) -> list[dict[str, Any]]:
    windows = result.get("windows")
    if not isinstance(windows, list):
        raise PangramError("Pangram's completed result has an invalid 'windows' field.")

    cleaned: list[dict[str, Any]] = []
    for index, item in enumerate(windows):
        if not isinstance(item, dict):
            raise PangramError(
                f"Pangram's completed result has an invalid window at index {index}."
            )
        # Validate the documented source-text field without retaining it.
        if not isinstance(item.get("text"), str):
            raise PangramError(
                f"Pangram's completed result has an invalid window at index {index}."
            )
        label = _required_window_string(item, "label", index, max_length=100)
        confidence = _required_window_string(
            item, "confidence", index, max_length=30
        )
        score = _required_window_fraction(item, "ai_assistance_score", index)
        start_index = _required_window_count(item, "start_index", index)
        end_index = _required_window_count(item, "end_index", index)
        word_count = _required_window_count(item, "word_count", index)
        token_length = _required_window_count(item, "token_length", index)
        if end_index < start_index:
            raise PangramError(
                f"Pangram's completed result has an invalid window at index {index}."
            )
        cleaned.append(
            {
                "label": label,
                "ai_assistance_score": score,
                "confidence": confidence,
                "start_index": start_index,
                "end_index": end_index,
                "word_count": word_count,
                "token_length": token_length,
            }
        )
    return cleaned


def _required_window_string(
    item: dict[str, Any], key: str, index: int, *, max_length: int
) -> str:
    value = item.get(key)
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > max_length
    ):
        raise PangramError(
            f"Pangram's completed result has an invalid '{key}' field in window {index}."
        )
    return value.strip()


def _required_window_fraction(
    item: dict[str, Any], key: str, index: int
) -> float:
    value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PangramError(
            f"Pangram's completed result has an invalid '{key}' field in window {index}."
        )
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise PangramError(
            f"Pangram's completed result has an invalid '{key}' field in window {index}."
        )
    return numeric


def _required_window_count(item: dict[str, Any], key: str, index: int) -> int:
    value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PangramError(
            f"Pangram's completed result has an invalid '{key}' field in window {index}."
        )
    return value


def _validate_success(result: dict[str, Any]) -> dict[str, Any]:
    stage = result.get("stage")
    if stage != TERMINAL_SUCCESS:
        raise PangramError("Pangram returned an inconsistent completed result.")

    prediction_short = _required_string(result, "prediction_short", max_length=30)
    if prediction_short not in KNOWN_CLASSIFICATIONS:
        raise PangramError(
            "Pangram's completed result has an invalid 'prediction_short' field."
        )

    # Validate the response and omit source-text fields from output.
    version = _required_string(result, "version", max_length=100)
    headline = _required_string(result, "headline", max_length=300)
    _required_string(result, "prediction", max_length=3000)
    fraction_ai = _required_fraction(result, "fraction_ai")
    fraction_ai_assisted = _required_fraction(result, "fraction_ai_assisted")
    fraction_human = _required_fraction(result, "fraction_human")
    num_ai_segments = _required_count(result, "num_ai_segments")
    num_ai_assisted_segments = _required_count(result, "num_ai_assisted_segments")
    num_human_segments = _required_count(result, "num_human_segments")
    if not isinstance(result.get("text"), str):
        raise PangramError("Pangram's completed result has an invalid 'text' field.")
    windows = _clean_windows(result)

    return {
        "stage": TERMINAL_SUCCESS,
        "version": version,
        "headline": headline,
        "prediction_short": prediction_short,
        "fraction_ai": fraction_ai,
        "fraction_ai_assisted": fraction_ai_assisted,
        "fraction_human": fraction_human,
        "num_ai_segments": num_ai_segments,
        "num_ai_assisted_segments": num_ai_assisted_segments,
        "num_human_segments": num_human_segments,
        "windows": windows,
    }


def _task_stage(result: dict[str, Any], task_id: str) -> str:
    stage = result.get("stage")
    if not isinstance(stage, str) or not stage.startswith("STAGE_"):
        raise PangramError("Pangram returned an invalid task status response.")
    returned_task_id = result.get("task_id")
    if returned_task_id is not None and returned_task_id != task_id:
        raise PangramError("Pangram returned a mismatched task status response.")
    return stage


def predict(
    text: str,
    timeout: float,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_polls: int = DEFAULT_MAX_POLLS,
) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise PangramError("The submitted text is empty.")
    if not math.isfinite(timeout) or timeout <= 0:
        raise PangramError("The request timeout must be greater than zero.")
    if not math.isfinite(poll_interval) or poll_interval < 0:
        raise PangramError("The poll interval must be zero or greater.")
    if isinstance(max_polls, bool) or not isinstance(max_polls, int) or max_polls <= 0:
        raise PangramError("The maximum poll count must be greater than zero.")

    body = json.dumps(
        {"text": text, "public_dashboard_link": False}, ensure_ascii=False
    ).encode("utf-8")
    create_request = urllib.request.Request(
        CREATE_TASK_URL,
        data=body,
        headers=_headers(),
        method="POST",
    )
    created = _request_json(create_request, timeout, "creating the analysis task")
    task_id = created.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise PangramError("Pangram returned an invalid task-creation response.")
    task_id = task_id.strip()
    task_url = f"{CREATE_TASK_URL}/{urllib.parse.quote(task_id, safe='')}"

    for poll_number in range(max_polls):
        status_request = urllib.request.Request(
            task_url,
            headers=_headers(),
            method="GET",
        )
        result = _request_json(status_request, timeout, "checking the analysis task")
        stage = _task_stage(result, task_id)
        if stage == TERMINAL_SUCCESS:
            return _validate_success(result)
        if stage == TERMINAL_FAILURE:
            # Provider failure details may contain submitted text; keep this generic.
            raise PangramError("Pangram could not analyze the submitted text.")
        if poll_number + 1 < max_polls and poll_interval > 0:
            time.sleep(poll_interval)

    raise PangramError(
        f"Pangram analysis did not finish after {max_polls} status checks."
    )


def fraction(result: dict[str, Any], key: str) -> float | None:
    value = result.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) and 0.0 <= numeric <= 1.0 else None


def percent(value: float | None) -> str:
    return "unavailable" if value is None else f"{value * 100:.1f}%"


def sanitized_result(
    result: dict[str, Any], include_segments: bool
) -> dict[str, Any]:
    allowed = {
        "stage",
        "version",
        "headline",
        "prediction_short",
        "fraction_ai",
        "fraction_ai_assisted",
        "fraction_human",
        "num_ai_segments",
        "num_ai_assisted_segments",
        "num_human_segments",
    }
    output = {key: result[key] for key in allowed if key in result}
    if include_segments:
        output["windows"] = [
            {key: value for key, value in item.items() if key != "text"}
            for item in result.get("windows", [])
            if isinstance(item, dict)
        ]
    return output


def print_summary(result: dict[str, Any], include_segments: bool) -> None:
    classification = result.get("prediction_short") or result.get("headline") or "Unknown"
    print(f"Classification: {classification}")
    if result.get("headline") and result.get("headline") != classification:
        print(f"Headline: {result['headline']}")
    print(f"AI-generated: {percent(fraction(result, 'fraction_ai'))}")
    print(f"AI-assisted: {percent(fraction(result, 'fraction_ai_assisted'))}")
    print(f"Human: {percent(fraction(result, 'fraction_human'))}")
    if result.get("version"):
        print(f"Pangram version: {result['version']}")

    if include_segments:
        windows = result.get("windows")
        if isinstance(windows, list) and windows:
            print("Segments (source text omitted):")
            for index, item in enumerate(windows, start=1):
                if not isinstance(item, dict):
                    continue
                label = item.get("label", "Unknown")
                confidence = item.get("confidence", "Unknown")
                score = fraction(item, "ai_assistance_score")
                start_index = item.get("start_index", "?")
                end_index = item.get("end_index", "?")
                word_count = item.get("word_count", "?")
                print(
                    f"{index}. {label}; confidence={confidence}; "
                    f"AI-assistance={percent(score)}; range={start_index}:{end_index}; "
                    f"words={word_count}"
                )
    print("Detector signal only — not definitive proof.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze text with Pangram's asynchronous AI-detection API."
    )
    source = parser.add_argument_group("input")
    source.add_argument("--text", help="Text to analyze (visible in shell history and process lists)")
    source.add_argument("--file", help="UTF-8 text file to analyze")
    parser.add_argument(
        "--segments",
        action="store_true",
        help="Include segment-level classifications without source-text snippets",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON without source-text fields",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between status checks (default: {DEFAULT_POLL_INTERVAL:g})",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=DEFAULT_MAX_POLLS,
        help=f"Maximum status checks (default: {DEFAULT_MAX_POLLS})",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero.")
    if not math.isfinite(args.poll_interval) or args.poll_interval < 0:
        raise SystemExit("--poll-interval must be zero or greater.")
    if args.max_polls <= 0:
        raise SystemExit("--max-polls must be greater than zero.")
    text = load_text(args)
    try:
        result = predict(text, args.timeout, args.poll_interval, args.max_polls)
    except PangramError as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        print(
            json.dumps(
                sanitized_result(result, args.segments), indent=2, sort_keys=True
            )
        )
    else:
        print_summary(result, args.segments)


if __name__ == "__main__":
    main()
