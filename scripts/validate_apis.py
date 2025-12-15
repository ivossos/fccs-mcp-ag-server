"""
Validate exposed FCCS Agent APIs using curl and emit a Markdown report.

Usage examples:
    python scripts/validate_apis.py --base-url http://localhost:8080
    python scripts/validate_apis.py --base-url https://example.com --report-path reports/api_validation.md

The script shells out to curl (configurable via --curl-bin) to keep parity with
runtime behavior and collects status codes, durations, and response snippets.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
DEFAULT_CURL_BIN = os.getenv("CURL_BIN", "curl")


@dataclass
class ApiTest:
    name: str
    method: str
    path: str
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    enabled: bool = True


@dataclass
class ApiTestResult:
    test: ApiTest
    status_code: Optional[int]
    duration: Optional[float]
    success: bool
    body_snippet: str
    error: Optional[str]
    curl_exit_code: int


def build_tests(include_execute: bool, tool_name: str, tool_args: Optional[str]) -> List[ApiTest]:
    parsed_args: Optional[Dict[str, Any]] = None
    if tool_args:
        try:
            parsed_args = json.loads(tool_args)
        except json.JSONDecodeError:
            parsed_args = None

    execute_body = {
        "tool_name": tool_name,
        "arguments": parsed_args or {},
        "session_id": "validation-script",
    }

    return [
        ApiTest(name="Health check", method="GET", path="/health"),
        ApiTest(name="List tools", method="GET", path="/tools"),
        ApiTest(
            name="MCP tools/list",
            method="POST",
            path="/message",
            body={"method": "tools/list", "params": {}},
            headers={"Content-Type": "application/json"},
        ),
        ApiTest(
            name="Execute tool",
            method="POST",
            path="/execute",
            body=execute_body,
            headers={"Content-Type": "application/json"},
            enabled=include_execute,
        ),
    ]


def run_curl(test: ApiTest, base_url: str, curl_bin: str) -> ApiTestResult:
    url = f"{base_url.rstrip('/')}{test.path}"
    cmd = [
        curl_bin,
        "-sS",
        "-w",
        "\nCURL_STATUS:%{http_code}\nCURL_TIME:%{time_total}\n",
        "-X",
        test.method,
        url,
    ]

    if test.headers:
        for key, value in test.headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    if test.body is not None:
        cmd.extend(["-d", json.dumps(test.body)])

    start = time.perf_counter()
    completed = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - start

    stdout_lines = completed.stdout.splitlines()
    status_code: Optional[int] = None
    duration: Optional[float] = None

    if stdout_lines:
        # Expect the last two lines to be CURL_STATUS and CURL_TIME
        maybe_status = stdout_lines[-2] if len(stdout_lines) >= 2 else None
        maybe_time = stdout_lines[-1] if stdout_lines else None

        if maybe_status and maybe_status.startswith("CURL_STATUS:"):
            try:
                status_code = int(maybe_status.replace("CURL_STATUS:", "").strip())
            except ValueError:
                status_code = None

        if maybe_time and maybe_time.startswith("CURL_TIME:"):
            try:
                duration = float(maybe_time.replace("CURL_TIME:", "").strip())
            except ValueError:
                duration = None

        body_content_lines = stdout_lines[:-2] if len(stdout_lines) >= 2 else []
        body_content = "\n".join(body_content_lines).strip()
    else:
        body_content = ""

    error_message = completed.stderr.strip() or None
    success = completed.returncode == 0 and status_code is not None and 200 <= status_code < 300

    # Format body snippet as JSON when possible for readability.
    formatted_body: str
    try:
        parsed_json = json.loads(body_content)
        formatted_body = json.dumps(parsed_json, indent=2)
    except Exception:
        formatted_body = body_content or ""

    max_snippet_len = 1200
    if len(formatted_body) > max_snippet_len:
        formatted_body = formatted_body[: max_snippet_len - 20] + "\n... [truncated] ..."

    return ApiTestResult(
        test=test,
        status_code=status_code,
        duration=duration if duration is not None else elapsed,
        success=success,
        body_snippet=formatted_body,
        error=error_message,
        curl_exit_code=completed.returncode,
    )


def write_report(results: List[ApiTestResult], report_path: Path, base_url: str, curl_bin: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# API Validation Report\n\n")
        f.write(f"- Generated: {timestamp}\n")
        f.write(f"- Base URL: `{base_url}`\n")
        f.write(f"- curl: `{curl_bin}`\n\n")

        f.write("| Test | Method | Path | Status | Duration (s) | Success | Notes |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for res in results:
            status_display = res.status_code if res.status_code is not None else "n/a"
            duration_display = f"{res.duration:.3f}" if res.duration is not None else "n/a"
            note = res.error or ""
            f.write(
                f"| {res.test.name} | {res.test.method} | {res.test.path} | {status_display} | "
                f"{duration_display} | {'✅' if res.success else '❌'} | {note} |\n"
            )

        f.write("\n")
        for res in results:
            f.write(f"## {res.test.name}\n\n")
            f.write(f"- Request: `{res.test.method} {res.test.path}`\n")
            f.write(f"- Status: {res.status_code if res.status_code is not None else 'n/a'}\n")
            f.write(f"- Duration: {res.duration:.3f}s\n")
            f.write(f"- curl exit code: {res.curl_exit_code}\n")
            if res.error:
                f.write(f"- Error: {res.error}\n")
            f.write("\nResponse snippet:\n\n")
            snippet = res.body_snippet or "(no body)"
            f.write("```json\n")
            f.write(snippet + "\n")
            f.write("```\n\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate FCCS Agent APIs via curl and emit a report.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of the API (default: %(default)s)")
    parser.add_argument(
        "--report-path",
        default=None,
        help="Path to write the Markdown report (default: ./API_VALIDATION_REPORT_<timestamp>.md)",
    )
    parser.add_argument("--curl-bin", default=DEFAULT_CURL_BIN, help="curl binary to use (default: %(default)s)")
    parser.add_argument(
        "--skip-execute",
        action="store_true",
        help="Skip the /execute tool call (useful when backend credentials are unavailable).",
    )
    parser.add_argument(
        "--tool-name",
        default="get_application_info",
        help="Tool name to exercise via /execute (default: %(default)s)",
    )
    parser.add_argument(
        "--tool-args",
        default=None,
        help="JSON string with arguments for the tool passed to /execute.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    default_report = Path(f"API_VALIDATION_REPORT_{timestamp}.md")
    report_path = Path(args.report_path) if args.report_path else default_report

    tests = build_tests(include_execute=not args.skip_execute, tool_name=args.tool_name, tool_args=args.tool_args)

    results: List[ApiTestResult] = []
    for test in tests:
        if not test.enabled:
            continue
        result = run_curl(test, base_url=args.base_url, curl_bin=args.curl_bin)
        results.append(result)

    write_report(results, report_path, base_url=args.base_url, curl_bin=args.curl_bin)

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "report": str(report_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

