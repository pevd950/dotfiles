#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which
from typing import Any, Iterable, Sequence

FAILURE_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_STATES = {
    "failure",
    "error",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_BUCKETS = {"fail"}

FAILURE_MARKERS = (
    "error",
    "fail",
    "failed",
    "traceback",
    "exception",
    "assert",
    "panic",
    "fatal",
    "timeout",
    "segmentation fault",
)

DEFAULT_MAX_LINES = 160
DEFAULT_CONTEXT_LINES = 30
PENDING_LOG_MARKERS = (
    "still in progress",
    "log will be available when it is complete",
)
XCODE_JOB_KEYWORDS = (
    "ios",
    "xcode",
    "xctest",
    "swift package tests",
    "unit tests",
    "ui tests",
)
XCODE_LOG_MARKERS = (
    "xcodebuild",
    "xctest",
    "exit code 65",
    "** test failed **",
    "test session results",
    "idetestoperationsobserverdebug",
)
ARTIFACT_NAME_MARKERS = (
    "xcresult",
    "result",
    "results",
    "bundle",
    "coverage-bundle",
)


class GhResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_gh_command(args: Sequence[str], cwd: Path) -> GhResult:
    process = subprocess.run(
        ["gh", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return GhResult(process.returncode, process.stdout, process.stderr)


def run_gh_command_raw(args: Sequence[str], cwd: Path) -> tuple[int, bytes, str]:
    process = subprocess.run(
        ["gh", *args],
        cwd=cwd,
        capture_output=True,
    )
    stderr = process.stderr.decode(errors="replace")
    return process.returncode, process.stdout, stderr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect failing GitHub PR checks, fetch GitHub Actions logs, and extract a "
            "failure snippet."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", default=".", help="Path inside the target Git repository.")
    parser.add_argument(
        "--pr", default=None, help="PR number or URL (defaults to current branch PR)."
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT_LINES)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_git_root(Path(args.repo))
    if repo_root is None:
        print("Error: not inside a Git repository.", file=sys.stderr)
        return 1

    if not ensure_gh_available(repo_root):
        return 1

    pr_value = resolve_pr(args.pr, repo_root)
    if pr_value is None:
        return 1

    checks = fetch_checks(pr_value, repo_root)
    if checks is None:
        return 1

    failing = [c for c in checks if is_failing(c)]
    if not failing:
        print(f"PR #{pr_value}: no failing checks detected.")
        return 0

    results = []
    for check in failing:
        results.append(
            analyze_check(
                check,
                repo_root=repo_root,
                max_lines=max(1, args.max_lines),
                context=max(1, args.context),
            )
        )

    if args.json:
        print(json.dumps({"pr": pr_value, "results": results}, indent=2))
    else:
        render_results(pr_value, results)

    return 1


def find_git_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def ensure_gh_available(repo_root: Path) -> bool:
    if which("gh") is None:
        print("Error: gh is not installed or not on PATH.", file=sys.stderr)
        return False
    result = run_gh_command(["auth", "status"], cwd=repo_root)
    if result.returncode == 0:
        return True
    message = (result.stderr or result.stdout or "").strip()
    print(message or "Error: gh not authenticated.", file=sys.stderr)
    return False


def resolve_pr(pr_value: str | None, repo_root: Path) -> str | None:
    if pr_value:
        return pr_value
    result = run_gh_command(["pr", "view", "--json", "number"], cwd=repo_root)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        print(message or "Error: unable to resolve PR.", file=sys.stderr)
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        print("Error: unable to parse PR JSON.", file=sys.stderr)
        return None
    number = data.get("number")
    if not number:
        print("Error: no PR number found.", file=sys.stderr)
        return None
    return str(number)


def fetch_checks(pr_value: str, repo_root: Path) -> list[dict[str, Any]] | None:
    primary_fields = ["name", "state", "conclusion", "detailsUrl", "startedAt", "completedAt"]
    result = run_gh_command(
        ["pr", "checks", pr_value, "--json", ",".join(primary_fields)],
        cwd=repo_root,
    )
    if result.returncode != 0:
        message = "\n".join(filter(None, [result.stderr, result.stdout])).strip()
        available_fields = parse_available_fields(message)
        if available_fields:
            fallback_fields = [
                "name",
                "state",
                "bucket",
                "link",
                "startedAt",
                "completedAt",
                "workflow",
            ]
            selected_fields = [field for field in fallback_fields if field in available_fields]
            if not selected_fields:
                print("Error: no usable fields available for gh pr checks.", file=sys.stderr)
                return None
            result = run_gh_command(
                ["pr", "checks", pr_value, "--json", ",".join(selected_fields)],
                cwd=repo_root,
            )
            if result.returncode != 0:
                message = (result.stderr or result.stdout or "").strip()
                print(message or "Error: gh pr checks failed.", file=sys.stderr)
                return None
        else:
            print(message or "Error: gh pr checks failed.", file=sys.stderr)
            return None
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        print("Error: unable to parse checks JSON.", file=sys.stderr)
        return None
    if not isinstance(data, list):
        print("Error: unexpected checks JSON shape.", file=sys.stderr)
        return None
    return data


def is_failing(check: dict[str, Any]) -> bool:
    conclusion = normalize_field(check.get("conclusion"))
    if conclusion in FAILURE_CONCLUSIONS:
        return True
    state = normalize_field(check.get("state") or check.get("status"))
    if state in FAILURE_STATES:
        return True
    bucket = normalize_field(check.get("bucket"))
    return bucket in FAILURE_BUCKETS


def analyze_check(
    check: dict[str, Any],
    repo_root: Path,
    max_lines: int,
    context: int,
) -> dict[str, Any]:
    url = check.get("detailsUrl") or check.get("link") or ""
    run_id = extract_run_id(url)
    job_id = extract_job_id(url)
    base: dict[str, Any] = {
        "name": check.get("name", ""),
        "detailsUrl": url,
        "runId": run_id,
        "jobId": job_id,
    }

    if run_id is None:
        base["status"] = "external"
        base["note"] = "No GitHub Actions run id detected in detailsUrl."
        return base

    metadata = fetch_run_metadata(run_id, repo_root)
    log_text, log_error, log_status = fetch_check_log(
        run_id=run_id,
        job_id=job_id,
        repo_root=repo_root,
    )

    if log_status == "pending":
        base["status"] = "log_pending"
        base["note"] = log_error or "Logs are not available yet."
        if metadata:
            base["run"] = metadata
        return base

    xcresult_info = maybe_extract_xcresult_summary(
        run_id=run_id,
        check=check,
        metadata=metadata,
        repo_root=repo_root,
        log_text=log_text,
        log_error=log_error,
    )

    if log_error:
        if xcresult_info:
            base["status"] = "xcresult_only"
            base["note"] = "Logs were incomplete; recovered failing test details from an xcresult artifact."
            base["xcresult"] = xcresult_info
        else:
            base["status"] = "log_unavailable"
            base["error"] = log_error
        if metadata:
            base["run"] = metadata
        return base

    snippet = extract_failure_snippet(log_text, max_lines=max_lines, context=context)
    base["status"] = "ok"
    base["run"] = metadata or {}
    base["logSnippet"] = snippet
    base["logTail"] = tail_lines(log_text, max_lines)
    if xcresult_info:
        base["xcresult"] = xcresult_info
    return base


def extract_run_id(url: str) -> str | None:
    if not url:
        return None
    for pattern in (r"/actions/runs/(\d+)", r"/runs/(\d+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_job_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"/actions/runs/\d+/job/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/job/(\d+)", url)
    if match:
        return match.group(1)
    return None


def fetch_run_metadata(run_id: str, repo_root: Path) -> dict[str, Any] | None:
    fields = [
        "conclusion",
        "status",
        "workflowName",
        "name",
        "event",
        "headBranch",
        "headSha",
        "url",
    ]
    result = run_gh_command(["run", "view", run_id, "--json", ",".join(fields)], cwd=repo_root)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def fetch_check_log(
    run_id: str,
    job_id: str | None,
    repo_root: Path,
) -> tuple[str, str, str]:
    log_text, log_error = fetch_run_log(run_id, repo_root)
    if not log_error:
        return log_text, "", "ok"

    if is_log_pending_message(log_error) and job_id:
        job_log, job_error = fetch_job_log(job_id, repo_root)
        if job_log:
            return job_log, "", "ok"
        if job_error and is_log_pending_message(job_error):
            return "", job_error, "pending"
        if job_error:
            return "", job_error, "error"
        return "", log_error, "pending"

    if is_log_pending_message(log_error):
        return "", log_error, "pending"

    return "", log_error, "error"


def fetch_run_log(run_id: str, repo_root: Path) -> tuple[str, str]:
    result = run_gh_command(["run", "view", run_id, "--log"], cwd=repo_root)
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "").strip()
        return "", error or "gh run view failed"
    return result.stdout, ""


def fetch_job_log(job_id: str, repo_root: Path) -> tuple[str, str]:
    repo_slug = fetch_repo_slug(repo_root)
    if not repo_slug:
        return "", "Error: unable to resolve repository name for job logs."
    endpoint = f"/repos/{repo_slug}/actions/jobs/{job_id}/logs"
    returncode, stdout_bytes, stderr = run_gh_command_raw(["api", endpoint], cwd=repo_root)
    if returncode != 0:
        message = (stderr or stdout_bytes.decode(errors="replace")).strip()
        return "", message or "gh api job logs failed"
    if is_zip_payload(stdout_bytes):
        return "", "Job logs returned a zip archive; unable to parse."
    return stdout_bytes.decode(errors="replace"), ""


def fetch_repo_slug(repo_root: Path) -> str | None:
    result = run_gh_command(["repo", "view", "--json", "nameWithOwner"], cwd=repo_root)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    name_with_owner = data.get("nameWithOwner")
    if not name_with_owner:
        return None
    return str(name_with_owner)


def maybe_extract_xcresult_summary(
    run_id: str,
    check: dict[str, Any],
    metadata: dict[str, Any] | None,
    repo_root: Path,
    log_text: str,
    log_error: str,
) -> dict[str, Any] | None:
    if which("xcrun") is None:
        return None
    if not should_try_xcresult(check, metadata, log_text, log_error):
        return None

    artifacts = fetch_run_artifacts(run_id, repo_root)
    if not artifacts:
        return None

    with tempfile.TemporaryDirectory(prefix=f"gh-fix-ci-{run_id}-") as temp_dir:
        temp_root = Path(temp_dir)
        for artifact in artifacts:
            artifact_name = normalize_text(artifact.get("name"))
            if not artifact_name or not artifact_name_matches(artifact_name):
                continue

            download_dir = temp_root / artifact_name
            download_dir.mkdir(parents=True, exist_ok=True)
            if not download_artifact(run_id, artifact_name, download_dir, repo_root):
                continue

            bundle_path = find_xcresult_bundle(download_dir)
            if bundle_path is None:
                continue

            summary = load_xcresult_summary(bundle_path)
            if summary is None:
                continue

            return {
                "artifactName": artifact_name,
                "artifactId": artifact.get("id"),
                "bundlePath": str(bundle_path),
                "summary": summarize_xcresult_summary(summary),
            }

    return None


def should_try_xcresult(
    check: dict[str, Any],
    metadata: dict[str, Any] | None,
    log_text: str,
    log_error: str,
) -> bool:
    haystack = " ".join(
        filter(
            None,
            [
                str(check.get("name") or ""),
                str(check.get("workflow") or ""),
                str((metadata or {}).get("workflowName") or ""),
                str((metadata or {}).get("name") or ""),
                tail_lines(log_text, 80),
                log_error,
            ],
        )
    ).lower()
    return any(keyword in haystack for keyword in XCODE_JOB_KEYWORDS) or any(
        marker in haystack for marker in XCODE_LOG_MARKERS
    )


def fetch_run_artifacts(run_id: str, repo_root: Path) -> list[dict[str, Any]]:
    repo_slug = fetch_repo_slug(repo_root)
    if not repo_slug:
        return []

    result = run_gh_command(["api", f"/repos/{repo_slug}/actions/runs/{run_id}/artifacts"], cwd=repo_root)
    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []

    artifacts = data.get("artifacts", [])
    if not isinstance(artifacts, list):
        return []
    return [artifact for artifact in artifacts if isinstance(artifact, dict)]


def artifact_name_matches(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in ARTIFACT_NAME_MARKERS)


def download_artifact(run_id: str, artifact_name: str, destination: Path, repo_root: Path) -> bool:
    result = run_gh_command(
        ["run", "download", run_id, "-n", artifact_name, "-D", str(destination)],
        cwd=repo_root,
    )
    return result.returncode == 0


def find_xcresult_bundle(root: Path) -> Path | None:
    candidates = [root]
    candidates.extend(
        path
        for path in sorted(root.rglob("*"), key=lambda candidate: (len(candidate.parts), str(candidate)))
        if path.is_dir()
    )
    for candidate in candidates:
        if is_xcresult_bundle(candidate):
            return prepare_summary_bundle_path(candidate, root)
    return None


def is_xcresult_bundle(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    process = subprocess.run(
        [
            "xcrun",
            "xcresulttool",
            "get",
            "content-availability",
            "--path",
            str(path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        return False

    try:
        data = json.loads(process.stdout or "{}")
    except json.JSONDecodeError:
        return False

    return bool(data.get("hasTestResults") or data.get("hasDiagnostics"))


def prepare_summary_bundle_path(path: Path, root: Path) -> Path:
    if path.name.endswith(".xcresult"):
        return path

    alias_name = f"{path.name or 'result'}.xcresult"
    alias_path = root / alias_name
    if not alias_path.exists():
        alias_path.symlink_to(path, target_is_directory=True)
    return alias_path


def load_xcresult_summary(path: Path) -> dict[str, Any] | None:
    process = subprocess.run(
        [
            "xcrun",
            "xcresulttool",
            "get",
            "test-results",
            "summary",
            "--path",
            str(path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if process.returncode != 0 or not process.stdout.strip():
        return None

    try:
        data = json.loads(process.stdout)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    return data


def summarize_xcresult_summary(summary: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "result": summary.get("result"),
        "totalTestCount": summary.get("totalTestCount"),
        "passedTests": summary.get("passedTests"),
        "failedTests": summary.get("failedTests"),
        "skippedTests": summary.get("skippedTests"),
        "environmentDescription": summary.get("environmentDescription"),
    }

    devices = summary.get("devicesAndConfigurations")
    if isinstance(devices, list) and devices:
        device_info = devices[0].get("device", {}) if isinstance(devices[0], dict) else {}
        if isinstance(device_info, dict):
            result["device"] = {
                "deviceName": device_info.get("deviceName"),
                "osVersion": device_info.get("osVersion"),
                "architecture": device_info.get("architecture"),
            }

    test_failures = summary.get("testFailures")
    if isinstance(test_failures, list):
        result["testFailures"] = [
            {
                "testIdentifierString": failure.get("testIdentifierString"),
                "testName": failure.get("testName"),
                "failureText": failure.get("failureText"),
            }
            for failure in test_failures[:20]
            if isinstance(failure, dict)
        ]

    top_insights = summary.get("topInsights")
    if isinstance(top_insights, list):
        result["topInsights"] = [
            {
                "text": insight.get("text"),
                "impact": insight.get("impact"),
            }
            for insight in top_insights[:5]
            if isinstance(insight, dict)
        ]

    return result


def normalize_field(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def parse_available_fields(message: str) -> list[str]:
    if "Available fields:" not in message:
        return []
    fields: list[str] = []
    collecting = False
    for line in message.splitlines():
        if "Available fields:" in line:
            collecting = True
            continue
        if not collecting:
            continue
        field = line.strip()
        if not field:
            continue
        fields.append(field)
    return fields


def is_log_pending_message(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in PENDING_LOG_MARKERS)


def is_zip_payload(payload: bytes) -> bool:
    return payload.startswith(b"PK")


def extract_failure_snippet(log_text: str, max_lines: int, context: int) -> str:
    lines = log_text.splitlines()
    if not lines:
        return ""

    marker_index = find_failure_index(lines)
    if marker_index is None:
        return "\n".join(lines[-max_lines:])

    start = max(0, marker_index - context)
    end = min(len(lines), marker_index + context)
    window = lines[start:end]
    if len(window) > max_lines:
        window = window[-max_lines:]
    return "\n".join(window)


def find_failure_index(lines: Sequence[str]) -> int | None:
    for idx in range(len(lines) - 1, -1, -1):
        lowered = lines[idx].lower()
        if any(marker in lowered for marker in FAILURE_MARKERS):
            return idx
    return None


def tail_lines(text: str, max_lines: int) -> str:
    if max_lines <= 0:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def render_results(pr_number: str, results: Iterable[dict[str, Any]]) -> None:
    results_list = list(results)
    print(f"PR #{pr_number}: {len(results_list)} failing checks analyzed.")
    for result in results_list:
        print("-" * 60)
        print(f"Check: {result.get('name', '')}")
        if result.get("detailsUrl"):
            print(f"Details: {result['detailsUrl']}")
        run_id = result.get("runId")
        if run_id:
            print(f"Run ID: {run_id}")
        job_id = result.get("jobId")
        if job_id:
            print(f"Job ID: {job_id}")
        status = result.get("status", "unknown")
        print(f"Status: {status}")

        run_meta = result.get("run", {})
        if run_meta:
            branch = run_meta.get("headBranch", "")
            sha = (run_meta.get("headSha") or "")[:12]
            workflow = run_meta.get("workflowName") or run_meta.get("name") or ""
            conclusion = run_meta.get("conclusion") or run_meta.get("status") or ""
            print(f"Workflow: {workflow} ({conclusion})")
            if branch or sha:
                print(f"Branch/SHA: {branch} {sha}")
            if run_meta.get("url"):
                print(f"Run URL: {run_meta['url']}")

        if result.get("note"):
            print(f"Note: {result['note']}")

        if result.get("error"):
            print(f"Error fetching logs: {result['error']}")
            continue

        snippet = result.get("logSnippet") or ""
        if snippet:
            print("Failure snippet:")
            print(indent_block(snippet, prefix="  "))
        else:
            print("No snippet available.")

        xcresult = result.get("xcresult")
        if isinstance(xcresult, dict):
            print("xcresult artifact summary:")
            artifact_name = xcresult.get("artifactName")
            if artifact_name:
                print(f"  Artifact: {artifact_name}")
            summary = xcresult.get("summary", {})
            if isinstance(summary, dict):
                failed = summary.get("failedTests")
                total = summary.get("totalTestCount")
                result_text = summary.get("result")
                if result_text or failed is not None or total is not None:
                    print(
                        "  "
                        + " / ".join(
                            part
                            for part in [
                                f"Result: {result_text}" if result_text else "",
                                f"Failed: {failed}" if failed is not None else "",
                                f"Total: {total}" if total is not None else "",
                            ]
                            if part
                        )
                    )

                failures = summary.get("testFailures")
                if isinstance(failures, list) and failures:
                    print("  Failing tests:")
                    for failure in failures:
                        if not isinstance(failure, dict):
                            continue
                        identifier = normalize_text(
                            failure.get("testIdentifierString") or failure.get("testName")
                        )
                        failure_text = normalize_text(failure.get("failureText"))
                        detail = f"{identifier}: {failure_text}" if failure_text else identifier
                        print(f"    - {detail}")

                insights = summary.get("topInsights")
                if isinstance(insights, list) and insights:
                    print("  Top insights:")
                    for insight in insights:
                        if not isinstance(insight, dict):
                            continue
                        text = normalize_text(insight.get("text"))
                        impact = normalize_text(insight.get("impact"))
                        if not text:
                            continue
                        if impact:
                            print(f"    - {text} ({impact})")
                        else:
                            print(f"    - {text}")
    print("-" * 60)


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
