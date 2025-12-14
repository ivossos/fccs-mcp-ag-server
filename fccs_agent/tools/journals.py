"""Journal tools - get_journals, get_journal_details, perform_journal_action, etc."""

from typing import Any, Optional

from fccs_agent.client.fccs_client import FccsClient

_client: FccsClient = None
_app_name: str = None


def set_client(client: FccsClient):
    global _client
    _client = client


def set_app_name(app_name: str):
    global _app_name
    _app_name = app_name


async def get_journals(
    scenario: Optional[str] = None,
    year: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100
) -> dict[str, Any]:
    """Retrieve consolidation journals with optional filters / Obter diarios de consolidacao.

    Args:
        scenario: Filter by scenario.
        year: Filter by year.
        period: Filter by period.
        status: Filter by status.
        offset: Offset for pagination (default: 0).
        limit: Limit results (default: 100).

    Returns:
        dict: List of journals.
    """
    filters = {}
    if scenario:
        filters["scenario"] = scenario
    if year:
        filters["year"] = year
    if period:
        filters["period"] = period
    if status:
        filters["status"] = status

    journals = await _client.get_journals(
        _app_name, filters if filters else None, offset, limit
    )
    return {"status": "success", "data": journals}


async def get_journal_details(
    journal_label: str,
    scenario: Optional[str] = None,
    year: Optional[str] = None,
    period: Optional[str] = None,
    line_items: bool = True
) -> dict[str, Any]:
    """Get detailed information about a specific journal / Obter detalhes de um diario.

    Args:
        journal_label: The journal label.
        scenario: Filter by scenario.
        year: Filter by year.
        period: Filter by period.
        line_items: Include line items (default: true).

    Returns:
        dict: Journal details.
    """
    filters = {}
    if scenario:
        filters["scenario"] = scenario
    if year:
        filters["year"] = year
    if period:
        filters["period"] = period

    details = await _client.get_journal_details(
        _app_name, journal_label, filters if filters else None, line_items
    )
    return {"status": "success", "data": details}


async def perform_journal_action(
    journal_label: str,
    action: str,
    parameters: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Perform an action on a journal (approve, reject, post, etc.) / Executar acao em um diario.

    Args:
        journal_label: The journal label.
        action: Action to perform (approve, reject, post, etc.).
        parameters: Additional parameters for the action.

    Returns:
        dict: Action result.
    """
    result = await _client.perform_journal_action(
        _app_name, journal_label, action, parameters
    )
    return {"status": "success", "data": result}


async def update_journal_period(
    journal_label: str,
    new_period: str,
    parameters: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Update the period of a journal / Atualizar o periodo de um diario.

    Args:
        journal_label: The journal label.
        new_period: New period to set.
        parameters: Additional parameters.

    Returns:
        dict: Update result.
    """
    result = await _client.update_journal_period(
        _app_name, journal_label, new_period, parameters
    )
    return {"status": "success", "data": result}


async def export_journals(
    parameters: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Export consolidation journals / Exportar diarios de consolidacao.

    Args:
        parameters: Export parameters (scenario, year, period, etc.).

    Returns:
        dict: Job submission result.
    """
    result = await _client.export_journals(_app_name, parameters)
    return {"status": "success", "data": result}


async def import_journals(
    parameters: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Import consolidation journals / Importar diarios de consolidacao.

    Args:
        parameters: Import parameters.

    Returns:
        dict: Job submission result.
    """
    result = await _client.import_journals(_app_name, parameters)
    return {"status": "success", "data": result}


TOOL_DEFINITIONS = [
    {
        "name": "get_journals",
        "description": "Retrieve consolidation journals with optional filters / Obter diarios de consolidacao",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "description": "Filter by scenario"},
                "year": {"type": "string", "description": "Filter by year"},
                "period": {"type": "string", "description": "Filter by period"},
                "status": {"type": "string", "description": "Filter by status"},
                "offset": {"type": "number", "description": "Offset for pagination (default: 0)"},
                "limit": {"type": "number", "description": "Limit results (default: 100)"},
            },
        },
    },
    {
        "name": "get_journal_details",
        "description": "Get detailed information about a specific journal / Obter detalhes de um diario",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_label": {"type": "string", "description": "The journal label"},
                "scenario": {"type": "string", "description": "Filter by scenario"},
                "year": {"type": "string", "description": "Filter by year"},
                "period": {"type": "string", "description": "Filter by period"},
                "line_items": {"type": "boolean", "description": "Include line items (default: true)"},
            },
            "required": ["journal_label"],
        },
    },
    {
        "name": "perform_journal_action",
        "description": "Perform an action on a journal (approve, reject, post, etc.) / Executar acao em um diario",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_label": {"type": "string", "description": "The journal label"},
                "action": {"type": "string", "description": "Action to perform"},
                "parameters": {"type": "object", "description": "Additional parameters"},
            },
            "required": ["journal_label", "action"],
        },
    },
    {
        "name": "update_journal_period",
        "description": "Update the period of a journal / Atualizar o periodo de um diario",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_label": {"type": "string", "description": "The journal label"},
                "new_period": {"type": "string", "description": "New period to set"},
                "parameters": {"type": "object", "description": "Additional parameters"},
            },
            "required": ["journal_label", "new_period"],
        },
    },
    {
        "name": "export_journals",
        "description": "Export consolidation journals / Exportar diarios de consolidacao",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameters": {"type": "object", "description": "Export parameters"},
            },
        },
    },
    {
        "name": "import_journals",
        "description": "Import consolidation journals / Importar diarios de consolidacao",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameters": {"type": "object", "description": "Import parameters"},
            },
        },
    },
]
