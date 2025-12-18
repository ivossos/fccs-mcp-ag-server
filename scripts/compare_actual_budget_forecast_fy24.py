"""Compare Actual vs Budget vs Forecast for Net Income FY24 YTD by Entity and highlight variances >10%."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


async def get_net_income_value(
    account: str,
    entity: str,
    year: str,
    scenario: str,
    period: str = "Dec"
) -> Optional[float]:
    """Get Net Income value for a specific entity, year, scenario, and period (YTD)."""
    try:
        result = await smart_retrieve(
            account=account,
            entity=entity,
            period=period,
            years=year,
            scenario=scenario
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else None
    except Exception as e:
        print(f"    [ERROR] Failed to retrieve {scenario} for {entity}: {str(e)}")
    return None


async def get_entity_scenario_data(entity: str) -> Dict:
    """Get Net Income for Actual, Budget, and Forecast scenarios for FY24 YTD."""
    print(f"  Processing {entity}...")
    
    # Get values for all three scenarios
    actual = await get_net_income_value("FCCS_Net Income", entity, "FY24", "Actual", "Dec")
    budget = await get_net_income_value("FCCS_Net Income", entity, "FY24", "Budget", "Dec")
    forecast = await get_net_income_value("FCCS_Net Income", entity, "FY24", "Forecast", "Dec")
    
    # Calculate variances
    variances = {}
    
    # Actual vs Budget
    if actual is not None and budget is not None:
        var_actual_budget = actual - budget
        var_actual_budget_pct = (var_actual_budget / abs(budget) * 100) if budget != 0 else None
        variances["actual_vs_budget"] = {
            "amount": var_actual_budget,
            "percent": var_actual_budget_pct,
            "highlight": abs(var_actual_budget_pct) > 10 if var_actual_budget_pct is not None else False
        }
    else:
        variances["actual_vs_budget"] = {"amount": None, "percent": None, "highlight": False}
    
    # Actual vs Forecast
    if actual is not None and forecast is not None:
        var_actual_forecast = actual - forecast
        var_actual_forecast_pct = (var_actual_forecast / abs(forecast) * 100) if forecast != 0 else None
        variances["actual_vs_forecast"] = {
            "amount": var_actual_forecast,
            "percent": var_actual_forecast_pct,
            "highlight": abs(var_actual_forecast_pct) > 10 if var_actual_forecast_pct is not None else False
        }
    else:
        variances["actual_vs_forecast"] = {"amount": None, "percent": None, "highlight": False}
    
    # Budget vs Forecast
    if budget is not None and forecast is not None:
        var_budget_forecast = budget - forecast
        var_budget_forecast_pct = (var_budget_forecast / abs(forecast) * 100) if forecast != 0 else None
        variances["budget_vs_forecast"] = {
            "amount": var_budget_forecast,
            "percent": var_budget_forecast_pct,
            "highlight": abs(var_budget_forecast_pct) > 10 if var_budget_forecast_pct is not None else False
        }
    else:
        variances["budget_vs_forecast"] = {"amount": None, "percent": None, "highlight": False}
    
    return {
        "entity": entity,
        "actual": actual,
        "budget": budget,
        "forecast": forecast,
        "variances": variances,
        "has_data": any([actual is not None, budget is not None, forecast is not None]),
        "has_highlight": any([v.get("highlight", False) for v in variances.values()])
    }


async def generate_report():
    """Generate comparison report for Actual vs Budget vs Forecast."""
    print("=" * 80)
    print("ACTUAL vs BUDGET vs FORECAST - NET INCOME FY24 YTD BY ENTITY")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get entities from cache
        print("Loading entities from cache...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        
        if cached_entities and cached_entities.get("items"):
            print(f"[OK] Found {len(cached_entities['items'])} entities in cache")
            # Filter out system entities and parent rollups
            exclude = [
                "FCCS_Global Assumptions", "FCCS_Entity Total", "Entity",
                "I/C East & West", "I/C Central"
            ]
            entities_to_query = [
                item.get("name") for item in cached_entities["items"]
                if item.get("name") and item.get("name") not in exclude
            ]
            print(f"Querying {len(entities_to_query)} entities (excluding system/parent entities)")
        else:
            print("[WARNING] No entity list available from cache")
            await close_agent()
            return
        
        if not entities_to_query:
            print("No entities to query.")
            await close_agent()
            return
        
        # Get data for all entities
        print()
        print(f"Retrieving Net Income data for {len(entities_to_query)} entities...")
        print("(This may take several minutes)")
        print()
        
        all_entity_data = []
        queried = 0
        
        for entity in entities_to_query:
            queried += 1
            if queried % 10 == 0:
                print(f"  Progress: {queried}/{len(entities_to_query)} (Found {len(all_entity_data)} with data)...")
            
            entity_data = await get_entity_scenario_data(entity)
            if entity_data["has_data"]:
                all_entity_data.append(entity_data)
        
        print()
        print(f"[OK] Found {len(all_entity_data)} entities with Net Income data")
        
        if not all_entity_data:
            print("No entities with Net Income data found.")
            await close_agent()
            return
        
        # Filter entities with variances >10%
        highlighted_entities = [e for e in all_entity_data if e["has_highlight"]]
        
        print()
        print(f"[INFO] Found {len(highlighted_entities)} entities with variances >10%")
        print()
        
        # Generate HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Actual_Budget_Forecast_Comparison_FY24_{timestamp}.html"
        
        html_content = generate_html_report(all_entity_data, highlighted_entities, timestamp)
        
        report_path = Path(report_filename)
        report_path.write_text(html_content, encoding="utf-8")
        
        print("=" * 80)
        print("REPORT GENERATED")
        print("=" * 80)
        print(f"File: {report_filename}")
        print(f"Path: {report_path.absolute()}")
        print()
        print("Summary:")
        print(f"  - Total entities analyzed: {len(all_entity_data)}")
        print(f"  - Entities with variances >10%: {len(highlighted_entities)}")
        print(f"  - Period: FY24 YTD (through December)")
        print(f"  - Scenarios: Actual, Budget, Forecast")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_html_report(all_data: List[Dict], highlighted_data: List[Dict], timestamp: str) -> str:
    """Generate HTML report from comparison data."""
    
    # Sort entities: highlighted first, then by actual value
    sorted_data = sorted(
        all_data,
        key=lambda x: (
            not x["has_highlight"],  # Highlighted first
            -(x["actual"] if x["actual"] is not None else float('-inf'))  # Then by actual value (desc)
        )
    )
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actual vs Budget vs Forecast - Net Income FY24 YTD</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .summary-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .metric {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 5px;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        thead {{
            background: #34495e;
            color: white;
        }}
        
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        th {{
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            background: #34495e;
            z-index: 10;
        }}
        
        th:first-child, td:first-child {{
            text-align: left;
        }}
        
        tbody tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .highlight-row {{
            background-color: #fff3cd !important;
            border-left: 4px solid #ffc107;
        }}
        
        .highlight-row:hover {{
            background-color: #ffeaa7 !important;
        }}
        
        .positive {{
            color: #27ae60;
            font-weight: 600;
        }}
        
        .negative {{
            color: #e74c3c;
            font-weight: 600;
        }}
        
        .neutral {{
            color: #7f8c8d;
        }}
        
        .highlight-variance {{
            background-color: #ffc107;
            color: #000;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
        
        .legend {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 5px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 3px;
            margin-right: 5px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Actual vs Budget vs Forecast - Net Income FY24 YTD by Entity</h1>
        <div class="subtitle">
            Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            Analysis Period: FY24 Year-to-Date (through December)<br>
            Highlighting: Variances >10% are highlighted in yellow
        </div>
        
        <div class="summary-box">
            <h2 style="color: white; border: none; padding: 0; margin: 0 0 15px 0;">Summary</h2>
            <div class="summary-metrics">
                <div class="metric">
                    <div class="metric-label">Total Entities</div>
                    <div class="metric-value">{len(all_data)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Entities with Variances >10%</div>
                    <div class="metric-value">{len(highlighted_data)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Analysis Period</div>
                    <div class="metric-value">FY24 YTD</div>
                </div>
            </div>
        </div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #fff3cd;"></span>
                Row highlighted (variance >10%)
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #ffc107;"></span>
                Variance value highlighted
            </span>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Entity</th>
                    <th>Actual</th>
                    <th>Budget</th>
                    <th>Forecast</th>
                    <th>Actual vs Budget</th>
                    <th>Actual vs Forecast</th>
                    <th>Budget vs Forecast</th>
                </tr>
            </thead>
            <tbody>
"""
    
    def format_value(val):
        if val is None:
            return '<span class="neutral">N/A</span>'
        return f"${val:,.2f}"
    
    def format_variance(amount, percent, highlight=False):
        if amount is None or percent is None:
            return '<span class="neutral">N/A</span>'
        
        sign = "+" if amount >= 0 else ""
        pct_str = f" ({percent:+.1f}%)"
        
        class_name = "positive" if amount >= 0 else "negative"
        if highlight:
            return f'<span class="highlight-variance">{sign}${amount:,.2f}{pct_str}</span>'
        else:
            return f'<span class="{class_name}">{sign}${amount:,.2f}{pct_str}</span>'
    
    for entity_data in sorted_data:
        entity = entity_data["entity"]
        actual = entity_data["actual"]
        budget = entity_data["budget"]
        forecast = entity_data["forecast"]
        variances = entity_data["variances"]
        is_highlighted = entity_data["has_highlight"]
        
        row_class = ' class="highlight-row"' if is_highlighted else ''
        
        html += f"""
                <tr{row_class}>
                    <td><strong>{entity}</strong></td>
                    <td>{format_value(actual)}</td>
                    <td>{format_value(budget)}</td>
                    <td>{format_value(forecast)}</td>
                    <td>{format_variance(
                        variances["actual_vs_budget"]["amount"],
                        variances["actual_vs_budget"]["percent"],
                        variances["actual_vs_budget"]["highlight"]
                    )}</td>
                    <td>{format_variance(
                        variances["actual_vs_forecast"]["amount"],
                        variances["actual_vs_forecast"]["percent"],
                        variances["actual_vs_forecast"]["highlight"]
                    )}</td>
                    <td>{format_variance(
                        variances["budget_vs_forecast"]["amount"],
                        variances["budget_vs_forecast"]["percent"],
                        variances["budget_vs_forecast"]["highlight"]
                    )}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Report generated by FCCS MCP Agent</p>
            <p>Data source: Oracle FCCS Application</p>
            <p>Note: Variances are calculated as (First - Second) / |Second| × 100%</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    asyncio.run(generate_report())




