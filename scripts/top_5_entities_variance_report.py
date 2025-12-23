"""Generate report for top 5 entities by Net Income FY25 with variance analysis."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


async def get_account_value(
    account: str,
    entity: str,
    year: str,
    period: str = "Dec"
) -> Optional[float]:
    """Get account value for a specific entity, year, and period."""
    try:
        result = await smart_retrieve(
            account=account,
            entity=entity,
            period=period,
            years=year,
            scenario="Actual"
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else None
    except Exception:
        pass
    return None


async def get_entity_metrics(entity: str) -> dict:
    """Get all metrics (Net Income, Gross Profit, Operating Expenses) for FY24 and FY25."""
    metrics = {
        "entity": entity,
        "fy24": {},
        "fy25": {},
        "variances": {}
    }
    
    accounts = ["FCCS_Net Income", "FCCS_Gross Profit", "FCCS_Operating Expenses"]
    
    for account in accounts:
        # Get FY24 value
        fy24_value = await get_account_value(account, entity, "FY24", "Dec")
        metrics["fy24"][account] = fy24_value
        
        # Get FY25 value
        fy25_value = await get_account_value(account, entity, "FY25", "Dec")
        metrics["fy25"][account] = fy25_value
        
        # Calculate variance
        if fy24_value is not None and fy25_value is not None:
            variance = fy25_value - fy24_value
            variance_pct = (variance / abs(fy24_value) * 100) if fy24_value != 0 else None
            metrics["variances"][account] = {
                "amount": variance,
                "percent": variance_pct
            }
        else:
            metrics["variances"][account] = {
                "amount": None,
                "percent": None
            }
    
    return metrics


async def generate_report():
    """Generate report for top 5 entities by Net Income FY25."""
    print("=" * 70)
    print("Top 5 Entities by Net Income FY25 - Variance Analysis Report")
    print("=" * 70)
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
                "FCCS_Global Assumptions", "FCCS_Total Geography", "Entity",
                "Industrial Segment", "Energy Segment", "Fire Protection Segment",
                "Administrative Segment", "I/C East & West", "I/C Central"
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
        
        # Step 1: Get Net Income for all entities for FY25
        print()
        print(f"Step 1: Querying Net Income (FY25) for {len(entities_to_query)} entities...")
        print("(This may take several minutes)")
        print()
        
        entity_net_income = []
        queried = 0
        
        for entity in entities_to_query:
            queried += 1
            if queried % 20 == 0:
                print(f"  Progress: {queried}/{len(entities_to_query)} (Found {len(entity_net_income)} with data)...")
            
            net_income = await get_account_value("FCCS_Net Income", entity, "FY25", "Dec")
            if net_income is not None:
                entity_net_income.append({
                    "entity": entity,
                    "net_income": net_income
                })
        
        print()
        print(f"[OK] Found {len(entity_net_income)} entities with Net Income data")
        
        if not entity_net_income:
            print("No entities with Net Income data found.")
            await close_agent()
            return
        
        # Step 2: Sort and get top 5
        entity_net_income.sort(key=lambda x: x["net_income"], reverse=True)
        top_5_entities = entity_net_income[:5]
        
        print()
        print("Top 5 Entities by Net Income (FY25):")
        print("-" * 70)
        for i, item in enumerate(top_5_entities, 1):
            print(f"  {i}. {item['entity']}: ${item['net_income']:,.2f}")
        print()
        
        # Step 3: Get detailed metrics for top 5
        print("Step 2: Retrieving detailed metrics for top 5 entities...")
        print("(Net Income, Gross Profit, Operating Expenses for FY24 and FY25)")
        print()
        
        detailed_metrics = []
        for i, item in enumerate(top_5_entities, 1):
            entity = item["entity"]
            print(f"  [{i}/5] Processing {entity}...")
            metrics = await get_entity_metrics(entity)
            detailed_metrics.append(metrics)
        
        print()
        print("[OK] All metrics retrieved")
        print()
        
        # Step 4: Generate HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Top_5_Entities_Variance_Report_{timestamp}.html"
        
        html_content = generate_html_report(detailed_metrics, timestamp)
        
        report_path = Path(report_filename)
        report_path.write_text(html_content, encoding="utf-8")
        
        print("=" * 70)
        print("REPORT GENERATED")
        print("=" * 70)
        print(f"File: {report_filename}")
        print(f"Path: {report_path.absolute()}")
        print()
        print("Summary:")
        print(f"  - Top 5 entities analyzed")
        print(f"  - Metrics: Net Income, Gross Profit, Operating Expenses")
        print(f"  - Years: FY24 vs FY25 (YTD through December)")
        print(f"  - Variances calculated for all metrics")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_html_report(metrics_list: list, timestamp: str) -> str:
    """Generate HTML report from metrics data."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top 5 Entities by Net Income FY25 - Variance Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .entity-section {{
            margin-bottom: 40px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            background-color: #fafafa;
        }}
        .entity-header {{
            background-color: #3498db;
            color: white;
            padding: 15px;
            margin: -20px -20px 20px -20px;
            border-radius: 6px 6px 0 0;
            font-size: 18px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background-color: #34495e;
            color: white;
            text-align: left;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
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
        .metric-label {{
            font-weight: 600;
            color: #2c3e50;
        }}
        .year-label {{
            color: #7f8c8d;
            font-size: 12px;
        }}
        .variance-cell {{
            font-weight: 600;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Top 5 Entities by Net Income FY25 - Variance Analysis</h1>
        <div class="subtitle">
            Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            Analysis Period: FY24 vs FY25 (Year-to-Date through December)
        </div>
"""
    
    for i, metrics in enumerate(metrics_list, 1):
        entity = metrics["entity"]
        fy24 = metrics["fy24"]
        fy25 = metrics["fy25"]
        variances = metrics["variances"]
        
        # Format values
        def format_value(val):
            if val is None:
                return "N/A"
            return f"${val:,.2f}"
        
        def format_variance(amount, percent):
            if amount is None:
                return "N/A"
            sign = "+" if amount >= 0 else ""
            pct_str = f" ({percent:+.1f}%)" if percent is not None else ""
            return f"{sign}${amount:,.2f}{pct_str}"
        
        def get_variance_class(amount):
            if amount is None:
                return "neutral"
            return "positive" if amount >= 0 else "negative"
        
        html += f"""
        <div class="entity-section">
            <div class="entity-header">#{i} - {entity}</div>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>FY24</th>
                        <th>FY25</th>
                        <th>Variance</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="metric-label">Net Income</td>
                        <td>{format_value(fy24.get("FCCS_Net Income"))}</td>
                        <td>{format_value(fy25.get("FCCS_Net Income"))}</td>
                        <td class="variance-cell {get_variance_class(variances.get("FCCS_Net Income", {}).get("amount"))}">
                            {format_variance(
                                variances.get("FCCS_Net Income", {}).get("amount"),
                                variances.get("FCCS_Net Income", {}).get("percent")
                            )}
                        </td>
                    </tr>
                    <tr>
                        <td class="metric-label">Gross Profit</td>
                        <td>{format_value(fy24.get("FCCS_Gross Profit"))}</td>
                        <td>{format_value(fy25.get("FCCS_Gross Profit"))}</td>
                        <td class="variance-cell {get_variance_class(variances.get("FCCS_Gross Profit", {}).get("amount"))}">
                            {format_variance(
                                variances.get("FCCS_Gross Profit", {}).get("amount"),
                                variances.get("FCCS_Gross Profit", {}).get("percent")
                            )}
                        </td>
                    </tr>
                    <tr>
                        <td class="metric-label">Operating Expenses</td>
                        <td>{format_value(fy24.get("FCCS_Operating Expenses"))}</td>
                        <td>{format_value(fy25.get("FCCS_Operating Expenses"))}</td>
                        <td class="variance-cell {get_variance_class(variances.get("FCCS_Operating Expenses", {}).get("amount"))}">
                            {format_variance(
                                variances.get("FCCS_Operating Expenses", {}).get("amount"),
                                variances.get("FCCS_Operating Expenses", {}).get("percent")
                            )}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
"""
    
    html += """
        <div class="footer">
            <p>Report generated by FCCS MCP Agent</p>
            <p>Data source: Oracle FCCS Application</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    asyncio.run(generate_report())












