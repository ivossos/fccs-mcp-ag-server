"""ADK Agent - Main agent definition with all FCCS tools."""

import sys
from typing import Any, Optional

from fccs_agent.config import config, FCCSConfig
from fccs_agent.client.fccs_client import FccsClient
from fccs_agent.services.feedback_service import (
    init_feedback_service,
    before_tool_callback,
    after_tool_callback,
    get_feedback_service
)

# Import all tool modules
from fccs_agent.tools import application, jobs, dimensions, journals, data, reports, consolidation, memo

# Global state
_fccs_client: Optional[FccsClient] = None
_app_name: Optional[str] = None


def get_client() -> FccsClient:
    """Get the FCCS client instance."""
    global _fccs_client
    if _fccs_client is None:
        _fccs_client = FccsClient(config)
    return _fccs_client


def get_app_name() -> Optional[str]:
    """Get the current application name."""
    return _app_name


async def initialize_agent(cfg: Optional[FCCSConfig] = None) -> str:
    """Initialize the agent and connect to FCCS.

    Returns:
        str: The application name or error message.
    """
    global _fccs_client, _app_name

    use_config = cfg or config

    # Initialize FCCS client
    _fccs_client = FccsClient(use_config)

    # Set client reference in all tool modules
    application.set_client(_fccs_client)
    jobs.set_client(_fccs_client)
    dimensions.set_client(_fccs_client)
    journals.set_client(_fccs_client)
    data.set_client(_fccs_client)
    reports.set_client(_fccs_client)
    consolidation.set_client(_fccs_client)

    # Initialize feedback service (optional - don't break if it fails)
    try:
        init_feedback_service(use_config.database_url)
        print("Feedback service initialized", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not initialize feedback service: {e}", file=sys.stderr)
        print("Tool execution will continue without feedback tracking", file=sys.stderr)
        # Set feedback service to None so callbacks know it's not available
        from fccs_agent.services.feedback_service import _feedback_service
        import fccs_agent.services.feedback_service as feedback_module
        feedback_module._feedback_service = None

    # Try to connect to FCCS and get application name
    try:
        print("Connecting to FCCS to retrieve application info...", file=sys.stderr)
        apps = await _fccs_client.get_applications()
        if apps and apps.get("items") and len(apps["items"]) > 0:
            _app_name = apps["items"][0]["name"]
            print(f"Connected to FCCS Application: {_app_name}", file=sys.stderr)

            # Set app name in tool modules that need it
            jobs.set_app_name(_app_name)
            dimensions.set_app_name(_app_name)
            journals.set_app_name(_app_name)
            data.set_app_name(_app_name)
            consolidation.set_app_name(_app_name)

            return _app_name
        else:
            print("No applications found", file=sys.stderr)
            return "No applications found"
    except Exception as e:
        print(f"Initialization warning: Could not connect to FCCS: {e}", file=sys.stderr)
        return f"Connection failed: {e}"


async def close_agent():
    """Clean up agent resources."""
    global _fccs_client
    if _fccs_client:
        await _fccs_client.close()
        _fccs_client = None


# Tool registry - maps tool names to handler functions
TOOL_HANDLERS = {
    # Application
    "get_application_info": application.get_application_info,
    "get_rest_api_version": application.get_rest_api_version,
    # Jobs
    "list_jobs": jobs.list_jobs,
    "get_job_status": jobs.get_job_status,
    "run_business_rule": jobs.run_business_rule,
    "run_data_rule": jobs.run_data_rule,
    # Dimensions
    "get_dimensions": dimensions.get_dimensions,
    "get_members": dimensions.get_members,
    "get_dimension_hierarchy": dimensions.get_dimension_hierarchy,
    # Journals
    "get_journals": journals.get_journals,
    "get_journal_details": journals.get_journal_details,
    "perform_journal_action": journals.perform_journal_action,
    "update_journal_period": journals.update_journal_period,
    "export_journals": journals.export_journals,
    "import_journals": journals.import_journals,
    # Data
    "export_data_slice": data.export_data_slice,
    "smart_retrieve": data.smart_retrieve,
    "copy_data": data.copy_data,
    "clear_data": data.clear_data,
    # Reports
    "generate_report": reports.generate_report,
    "get_report_job_status": reports.get_report_job_status,
    # Consolidation
    "export_consolidation_rulesets": consolidation.export_consolidation_rulesets,
    "import_consolidation_rulesets": consolidation.import_consolidation_rulesets,
    "validate_metadata": consolidation.validate_metadata,
    "generate_intercompany_matching_report": consolidation.generate_intercompany_matching_report,
    "import_supplementation_data": consolidation.import_supplementation_data,
    "deploy_form_template": consolidation.deploy_form_template,
    # Memo
    "generate_investment_memo": memo.generate_investment_memo,
}

# Collect all tool definitions
ALL_TOOL_DEFINITIONS = (
    application.TOOL_DEFINITIONS +
    jobs.TOOL_DEFINITIONS +
    dimensions.TOOL_DEFINITIONS +
    journals.TOOL_DEFINITIONS +
    data.TOOL_DEFINITIONS +
    reports.TOOL_DEFINITIONS +
    consolidation.TOOL_DEFINITIONS +
    memo.TOOL_DEFINITIONS
)


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    session_id: str = "default"
) -> dict[str, Any]:
    """Execute a tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute.
        arguments: Arguments to pass to the tool.
        session_id: Session ID for feedback tracking.

    Returns:
        dict: Tool execution result.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    # Track execution start (non-blocking)
    try:
        before_tool_callback(session_id, tool_name, arguments)
    except Exception:
        pass  # Ignore feedback service errors

    try:
        result = await handler(**arguments)
        # Track execution end (non-blocking)
        try:
            after_tool_callback(session_id, tool_name, arguments, result)
        except Exception:
            pass  # Ignore feedback service errors
        return result
    except Exception as e:
        error_result = {"status": "error", "error": str(e)}
        try:
            after_tool_callback(session_id, tool_name, arguments, error_result)
        except Exception:
            pass  # Ignore feedback service errors
        return error_result


def get_tool_definitions() -> list[dict]:
    """Get all tool definitions for MCP server."""
    return ALL_TOOL_DEFINITIONS


# Agent instruction for ADK
AGENT_INSTRUCTION = """You are an expert assistant for Oracle EPM Cloud Financial Consolidation and Close (FCCS).

You help users with:
- Querying financial data from FCCS cubes
- Running consolidation and business rules
- Managing journals (create, approve, post)
- Generating financial reports and memos
- Managing dimensions and metadata

Respond in the same language as the user (English or Portuguese).
Always provide clear explanations of what you're doing and the results.

Available tools:
- get_application_info: Get FCCS application details
- list_jobs, get_job_status: Monitor jobs
- run_business_rule, run_data_rule: Execute rules
- get_dimensions, get_members, get_dimension_hierarchy: Explore dimensions
- get_journals, get_journal_details, perform_journal_action: Journal management
- export_data_slice, smart_retrieve: Query financial data
- generate_report, get_report_job_status: Generate reports
- And more consolidation and data management tools
"""
