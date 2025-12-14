"""CLI Entry Point - Interactive command-line interface."""

import asyncio
import sys

from fccs_agent.agent import initialize_agent, close_agent, execute_tool


async def run_cli():
    """Run interactive CLI session."""
    print("FCCS Agent CLI - Type 'help' for commands, 'exit' to quit")
    print("-" * 50)

    # Initialize agent
    app_name = await initialize_agent()
    print(f"Connected to: {app_name}\n")

    while True:
        try:
            user_input = input("fccs> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                break

            if user_input.lower() == "help":
                print_help()
                continue

            # Parse command
            parts = user_input.split(maxsplit=1)
            tool_name = parts[0]
            args_str = parts[1] if len(parts) > 1 else "{}"

            try:
                import json
                arguments = json.loads(args_str) if args_str != "{}" else {}
            except json.JSONDecodeError:
                # Try to parse as key=value pairs
                arguments = {}
                if len(parts) > 1:
                    for pair in parts[1].split():
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            arguments[key] = value

            # Execute tool
            result = await execute_tool(tool_name, arguments)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

        except KeyboardInterrupt:
            print("\n")
            continue
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}\n")

    await close_agent()
    print("Goodbye!")


def print_help():
    """Print help message."""
    print("""
Available Commands:
-------------------
get_application_info          Get FCCS application info
list_jobs                     List recent jobs
get_job_status {"job_id":"X"} Get status of a job
get_dimensions                List dimensions
get_members {"dimension_name":"Account"}  Get dimension members
smart_retrieve {"account":"FCCS_Net Income"}  Smart data retrieval

Examples:
---------
fccs> get_application_info
fccs> get_dimensions
fccs> get_members {"dimension_name": "Account"}
fccs> smart_retrieve {"account": "FCCS_Net Income", "period": "Jan"}

Type 'exit' to quit.
""")


def main():
    """Entry point for CLI."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
