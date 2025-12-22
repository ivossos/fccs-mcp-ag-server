"""Data tools - export_data_slice, smart_retrieve, copy_data, clear_data."""

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


async def export_data_slice(
    grid_definition: dict[str, Any],
    cube_name: str = "Consol"
) -> dict[str, Any]:
    """Export a specific data slice (grid) from the application / Exportar um slice de dados.

    Args:
        grid_definition: The data grid definition with pov, columns, and rows.
        cube_name: The name of the cube (default: 'Consol').

    Returns:
        dict: The exported data slice with rows and column values.
    """
    result = await _client.export_data_slice(_app_name, cube_name, grid_definition)
    return {"status": "success", "data": result}


async def smart_retrieve(
    account: str,
    entity: str = "FCCS_Total Geography",
    period: str = "Jan",
    years: str = "FY24",
    scenario: str = "Actual"
) -> dict[str, Any]:
    """Smart data retrieval with automatic 14-dimension handling / Recuperacao inteligente de dados.

    Args:
        account: The Account member (e.g., 'FCCS_Net Income').
        entity: The Entity member (default: 'FCCS_Total Geography').
        period: The Period member (default: 'Jan').
        years: The Years member (default: 'FY24').
        scenario: The Scenario member (default: 'Actual').

    Returns:
        dict: The retrieved data for the specified dimensions.
    """
    # Build grid definition with hardcoded defaults for 14 dimensions
    grid_definition = {
        "suppressMissingBlocks": True,
        "pov": {
            "members": [
                [years], [scenario], ["FCCS_YTD"], ["FCCS_Entity Total"],
                ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                ["FCCS_Mvmts_Total"], [entity], ["Entity Currency"],
                ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                ["Total Custom 4"]
            ]
        },
        "columns": [{"members": [[period]]}],
        "rows": [{"members": [[account]]}]
    }
    result = await _client.export_data_slice(_app_name, "Consol", grid_definition)
    return {"status": "success", "data": result}


async def smart_retrieve_with_movement(
    account: str,
    movement: str,
    entity: str = "FCCS_Total Geography",
    period: str = "Jan",
    years: str = "FY24",
    scenario: str = "Actual"
) -> dict[str, Any]:
    """Smart data retrieval with configurable Movement dimension / Recuperacao inteligente com dimensao Movement customizavel.

    Args:
        account: The Account member (e.g., 'FCCS_Net Income').
        movement: The Movement member (e.g., 'FCCS_Mvmts_Subtotal').
        entity: The Entity member (default: 'FCCS_Total Geography').
        period: The Period member (default: 'Jan').
        years: The Years member (default: 'FY24').
        scenario: The Scenario member (default: 'Actual').

    Returns:
        dict: The retrieved data for the specified dimensions.
    """
    # Build grid definition with hardcoded defaults for 14 dimensions, except Movement
    grid_definition = {
        "suppressMissingBlocks": True,
        "pov": {
            "members": [
                [years], [scenario], ["FCCS_YTD"], ["FCCS_Entity Total"],
                ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                [movement], [entity], ["Entity Currency"],
                ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                ["Total Custom 4"]
            ]
        },
        "columns": [{"members": [[period]]}],
        "rows": [{"members": [[account]]}]
    }
    result = await _client.export_data_slice(_app_name, "Consol", grid_definition)
    return {"status": "success", "data": result}


async def copy_data(
    from_scenario: Optional[str] = None,
    to_scenario: Optional[str] = None,
    from_year: Optional[str] = None,
    to_year: Optional[str] = None,
    from_period: Optional[str] = None,
    to_period: Optional[str] = None
) -> dict[str, Any]:
    """Copy data between scenarios, years, or periods / Copiar dados entre cenarios.

    Args:
        from_scenario: Source scenario.
        to_scenario: Target scenario.
        from_year: Source year.
        to_year: Target year.
        from_period: Source period.
        to_period: Target period.

    Returns:
        dict: Job submission result.
    """
    parameters = {}
    if from_scenario:
        parameters["fromScenario"] = from_scenario
    if to_scenario:
        parameters["toScenario"] = to_scenario
    if from_year:
        parameters["fromYear"] = from_year
    if to_year:
        parameters["toYear"] = to_year
    if from_period:
        parameters["fromPeriod"] = from_period
    if to_period:
        parameters["toPeriod"] = to_period

    result = await _client.copy_data(_app_name, parameters)
    return {"status": "success", "data": result}


async def clear_data(
    scenario: Optional[str] = None,
    year: Optional[str] = None,
    period: Optional[str] = None
) -> dict[str, Any]:
    """Clear data for specified scenario, year, and period / Limpar dados.

    Args:
        scenario: Scenario to clear.
        year: Year to clear.
        period: Period to clear.

    Returns:
        dict: Job submission result.
    """
    parameters = {}
    if scenario:
        parameters["scenario"] = scenario
    if year:
        parameters["year"] = year
    if period:
        parameters["period"] = period

    result = await _client.clear_data(_app_name, parameters)
    return {"status": "success", "data": result}


TOOL_DEFINITIONS = [
    {
        "name": "export_data_slice",
        "description": "Export a specific data slice (grid) from the application / Exportar um slice de dados",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cube_name": {
                    "type": "string",
                    "description": "The name of the cube (default: 'Consol')",
                },
                "grid_definition": {
                    "type": "object",
                    "description": "The data grid definition with pov, columns, and rows",
                },
            },
            "required": ["grid_definition"],
        },
    },
    {
        "name": "smart_retrieve",
        "description": "Smart data retrieval with automatic 14-dimension handling / Recuperacao inteligente",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {
                    "type": "string",
                    "description": "The Account member (e.g., 'FCCS_Net Income')",
                },
                "entity": {
                    "type": "string",
                    "description": "The Entity member (default: 'FCCS_Total Geography')",
                },
                "period": {
                    "type": "string",
                    "description": "The Period member (default: 'Jan')",
                },
                "years": {
                    "type": "string",
                    "description": "The Years member (default: 'FY24')",
                },
                "scenario": {
                    "type": "string",
                    "description": "The Scenario member (default: 'Actual')",
                },
            },
            "required": ["account"],
        },
    },
    {
        "name": "smart_retrieve_with_movement",
        "description": "Smart data retrieval with configurable Movement dimension / Recuperacao inteligente com dimensao Movement customizavel",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {
                    "type": "string",
                    "description": "The Account member (e.g., 'FCCS_Net Income')",
                },
                "movement": {
                    "type": "string",
                    "description": "The Movement member (e.g., 'FCCS_Mvmts_Subtotal')",
                },
                "entity": {
                    "type": "string",
                    "description": "The Entity member (default: 'FCCS_Total Geography')",
                },
                "period": {
                    "type": "string",
                    "description": "The Period member (default: 'Jan')",
                },
                "years": {
                    "type": "string",
                    "description": "The Years member (default: 'FY24')",
                },
                "scenario": {
                    "type": "string",
                    "description": "The Scenario member (default: 'Actual')",
                },
            },
            "required": ["account", "movement"],
        },
    },
    {
        "name": "copy_data",
        "description": "Copy data between scenarios, years, or periods / Copiar dados",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_scenario": {"type": "string", "description": "Source scenario"},
                "to_scenario": {"type": "string", "description": "Target scenario"},
                "from_year": {"type": "string", "description": "Source year"},
                "to_year": {"type": "string", "description": "Target year"},
                "from_period": {"type": "string", "description": "Source period"},
                "to_period": {"type": "string", "description": "Target period"},
            },
        },
    },
    {
        "name": "clear_data",
        "description": "Clear data for specified scenario, year, and period / Limpar dados",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "description": "Scenario to clear"},
                "year": {"type": "string", "description": "Year to clear"},
                "period": {"type": "string", "description": "Period to clear"},
            },
        },
    },
]
