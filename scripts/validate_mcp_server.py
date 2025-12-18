"""
Validate FCCS Agent MCP Server using stdio communication and emit a Markdown report.

Usage examples:
    python scripts/validate_mcp_server.py
    python scripts/validate_mcp_server.py --tool-name get_application_info
    python scripts/validate_mcp_server.py --python-bin python --report-path reports/mcp_validation.md

The script communicates with the MCP server via stdio using the MCP protocol.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_PYTHON_BIN = os.getenv("PYTHON_BIN", "python")
DEFAULT_TOOL_NAME = "get_application_info"


@dataclass
class McpTest:
    name: str
    method: str
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True


@dataclass
class McpTestResult:
    test: McpTest
    duration: Optional[float]
    success: bool
    response_snippet: str
    error: Optional[str]
    exit_code: int


class McpClient:
    """Client for communicating with MCP server via stdio."""

    def __init__(self, python_bin: str):
        self.python_bin = python_bin
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    async def start(self) -> bool:
        """Start the MCP server process."""
        try:
            self.process = subprocess.Popen(
                [self.python_bin, "-m", "cli.mcp_server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
            )
            # Give server a moment to start
            await asyncio.sleep(1.0)
            return self.process.poll() is None
        except Exception as e:
            print(f"Failed to start MCP server: {e}", file=sys.stderr)
            return False

    async def stop(self):
        """Stop the MCP server process."""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception:
                pass

    def _next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id

    async def send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP server process is not running")

        request_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        request_json = json.dumps(request) + "\n"
        
        try:
            # Write request
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response (MCP uses newline-delimited JSON)
            # Read lines until we find a response with matching ID
            max_attempts = 50
            for _ in range(max_attempts):
                response_line = await asyncio.to_thread(self.process.stdout.readline)
                if not response_line:
                    raise RuntimeError("No response from MCP server (connection closed)")
                
                line = response_line.strip()
                if not line:
                    continue
                    
                try:
                    response = json.loads(line)
                    # Check if this is the response to our request
                    if response.get("id") == request_id:
                        return response
                    # Otherwise, it might be a notification or response to another request
                    # Continue reading
                except json.JSONDecodeError:
                    # Skip invalid JSON lines (might be stderr output)
                    continue
            
            raise RuntimeError(f"No response found for request ID {request_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with MCP server: {e}")

    async def initialize(self) -> bool:
        """Initialize the MCP server connection."""
        try:
            # MCP protocol requires initialize/initialized handshake
            init_response = await self.send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "validation-script", "version": "1.0.0"},
                }
            )
            if "result" not in init_response:
                return False
            
            # Send initialized notification (no response expected)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            self.process.stdin.write(json.dumps(initialized_notification) + "\n")
            self.process.stdin.flush()
            
            return True
        except Exception as e:
            print(f"Initialize error: {e}", file=sys.stderr)
            return False

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return await self.send_request("tools/list")

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        return await self.send_request(
            "tools/call", {"name": name, "arguments": arguments}
        )


def build_tests(tool_name: str, tool_args: Optional[str], include_multiple_tools: bool = True) -> List[McpTest]:
    """Build list of MCP tests to run."""
    parsed_args: Optional[Dict[str, Any]] = None
    if tool_args:
        try:
            parsed_args = json.loads(tool_args)
        except json.JSONDecodeError:
            parsed_args = None

    tests = [
        # Initialize is done separately before tests
        McpTest(name="List tools", method="tools/list"),
        McpTest(
            name=f"Call tool: {tool_name}",
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": parsed_args or {},
            },
        ),
    ]
    
    # Add additional tool tests if requested
    if include_multiple_tools:
        additional_tools = [
            ("get_rest_api_version", {}),
            ("get_dimensions", {}),
            ("list_jobs", {}),
        ]
        
        for add_tool_name, add_args in additional_tools:
            if add_tool_name != tool_name:  # Don't duplicate the main tool
                tests.append(
                    McpTest(
                        name=f"Call tool: {add_tool_name}",
                        method="tools/call",
                        params={
                            "name": add_tool_name,
                            "arguments": add_args,
                        },
                    )
                )
    
    return tests


async def run_test(client: McpClient, test: McpTest) -> McpTestResult:
    """Run a single MCP test."""
    start = time.perf_counter()
    error = None
    response_snippet = ""
    success = False
    exit_code = 0

    try:
        if test.method == "tools/list":
            response = await client.list_tools()
            response_snippet = json.dumps(response, indent=2)
            success = "result" in response and "tools" in response.get("result", {})
        elif test.method == "tools/call":
            params = test.params or {}
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            response = await client.call_tool(name, arguments)
            response_snippet = json.dumps(response, indent=2)
            success = "result" in response
        else:
            response = await client.send_request(test.method, test.params)
            response_snippet = json.dumps(response, indent=2)
            success = "result" in response or "error" not in response

    except Exception as e:
        error = str(e)
        success = False
        response_snippet = json.dumps({"error": str(e)}, indent=2)

    duration = time.perf_counter() - start

    # Truncate response if too long
    max_snippet_len = 1200
    if len(response_snippet) > max_snippet_len:
        response_snippet = response_snippet[: max_snippet_len - 20] + "\n... [truncated] ..."

    return McpTestResult(
        test=test,
        duration=duration,
        success=success,
        response_snippet=response_snippet,
        error=error,
        exit_code=exit_code,
    )


def write_report(
    results: List[McpTestResult],
    report_path: Path,
    python_bin: str,
    tool_name: str,
) -> None:
    """Write validation report to Markdown file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )

    with report_path.open("w", encoding="utf-8") as f:
        f.write("# MCP Server Validation Report\n\n")
        f.write(f"- Generated: {timestamp}\n")
        f.write(f"- Python: `{python_bin}`\n")
        f.write(f"- Test Tool: `{tool_name}`\n\n")

        f.write("| Test | Method | Duration (s) | Success | Notes |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for res in results:
            duration_display = f"{res.duration:.3f}" if res.duration is not None else "n/a"
            note = res.error or ""
            f.write(
                f"| {res.test.name} | {res.test.method} | {duration_display} | "
                f"{'✅' if res.success else '❌'} | {note} |\n"
            )

        f.write("\n")
        for res in results:
            f.write(f"## {res.test.name}\n\n")
            f.write(f"- Method: `{res.test.method}`\n")
            if res.test.params:
                f.write(f"- Params: `{json.dumps(res.test.params, indent=2)}`\n")
            f.write(f"- Duration: {res.duration:.3f}s\n")
            if res.error:
                f.write(f"- Error: {res.error}\n")
            f.write("\nResponse:\n\n")
            snippet = res.response_snippet or "(no response)"
            f.write("```json\n")
            f.write(snippet + "\n")
            f.write("```\n\n")


async def main_async() -> Dict[str, Any]:
    """Main async function."""
    args = parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    default_report = Path(f"MCP_VALIDATION_REPORT_{timestamp}.md")
    report_path = Path(args.report_path) if args.report_path else default_report

    tests = build_tests(args.tool_name, args.tool_args, include_multiple_tools=not args.single_tool_only)

    client = McpClient(args.python_bin)

    try:
        # Start MCP server
        print("Starting MCP server...", file=sys.stderr)
        if not await client.start():
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "error": "Failed to start MCP server",
                "report": str(report_path),
            }

        # Wait a bit for server to be ready and initialize
        await asyncio.sleep(1.5)
        
        # Initialize connection (first test)
        print("Initializing MCP connection...", file=sys.stderr)
        init_success = await client.initialize()
        if not init_success:
            print("Warning: Initialize failed, continuing anyway...", file=sys.stderr)
        await asyncio.sleep(0.5)

        results: List[McpTestResult] = []
        for test in tests:
            if not test.enabled:
                continue
            print(f"Running test: {test.name}...", file=sys.stderr)
            result = await run_test(client, test)
            results.append(result)

        write_report(results, report_path, args.python_bin, args.tool_name)

        return {
            "total": len(results),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "report": str(report_path),
        }

    finally:
        await client.stop()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate FCCS Agent MCP Server via stdio and emit a report."
    )
    parser.add_argument(
        "--python-bin",
        default=DEFAULT_PYTHON_BIN,
        help=f"Python binary to use (default: {DEFAULT_PYTHON_BIN})",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Path to write the Markdown report (default: ./MCP_VALIDATION_REPORT_<timestamp>.md)",
    )
    parser.add_argument(
        "--tool-name",
        default=DEFAULT_TOOL_NAME,
        help=f"Tool name to test (default: {DEFAULT_TOOL_NAME})",
    )
    parser.add_argument(
        "--tool-args",
        default=None,
        help="JSON string with arguments for the tool.",
    )
    parser.add_argument(
        "--single-tool-only",
        action="store_true",
        help="Only test the specified tool, don't test additional tools.",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    try:
        result = asyncio.run(main_async())
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

