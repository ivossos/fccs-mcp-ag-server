"""Income Statement Comparison Report - Actual vs Forecast or Prior Year.

This script generates a comprehensive Income Statement comparison report showing:
- Revenue (Sales)
- Cost of Sales
- Gross Profit
- Operating Expenses
- Operating Income
- Net Income

With variances between Actual vs Forecast or Actual vs Prior Year.
"""

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


# Income Statement accounts in order
INCOME_STATEMENT_ACCOUNTS = [
    ("FCCS_Sales", "Revenue (Sales)"),
    ("FCCS_Cost of Sales", "Cost of Sales"),
    ("FCCS_Gross Profit", "Gross Profit"),
    ("FCCS_Operating Expenses", "Operating Expenses"),
    ("FCCS_Operating Income", "Operating Income"),
    ("FCCS_Net Income", "Net Income"),
]


async def get_account_value(
    account: str,
    entity: str,
    year: str,
    scenario: str,
    period: str = "Dec"
) -> Optional[float]:
    """Get account value for a specific entity, year, scenario, and period."""
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
        print(f"    [ERROR] Failed to retrieve {account} ({scenario}): {str(e)}")
    return None


async def get_income_statement_data(
    entity: str,
    year: str,
    scenario: str,
    period: str = "Dec"
) -> Dict[str, Optional[float]]:
    """Get all Income Statement accounts for a given entity, year, and scenario."""
    print(f"  Retrieving {scenario} data for {entity}...")
    
    income_statement = {}
    
    for account_code, account_label in INCOME_STATEMENT_ACCOUNTS:
        value = await get_account_value(account_code, entity, year, scenario, period)
        income_statement[account_code] = value
    
    return income_statement


def calculate_variance(actual: Optional[float], comparison: Optional[float]) -> Dict:
    """Calculate variance between actual and comparison values."""
    if actual is None or comparison is None:
        return {
            "amount": None,
            "percent": None,
            "highlight": False
        }
    
    variance_amount = actual - comparison
    variance_percent = None
    
    if comparison != 0:
        variance_percent = (variance_amount / abs(comparison)) * 100
    
    # Highlight variances >10% or >$1M
    highlight = (
        (variance_percent is not None and abs(variance_percent) > 10) or
        abs(variance_amount) > 1000000
    )
    
    return {
        "amount": variance_amount,
        "percent": variance_percent,
        "highlight": highlight
    }


def generate_html_report(
    entity: str,
    year: str,
    period: str,
    comparison_type: str,
    comparison_year: str,
    actual_data: Dict[str, Optional[float]],
    comparison_data: Dict[str, Optional[float]],
    timestamp: str
) -> str:
    """Generate HTML report from Income Statement comparison data."""
    
    # Calculate variances for all accounts
    variances = {}
    for account_code, account_label in INCOME_STATEMENT_ACCOUNTS:
        variances[account_code] = calculate_variance(
            actual_data.get(account_code),
            comparison_data.get(account_code)
        )
    
    # Determine comparison label
    if comparison_type == "forecast":
        comparison_label = f"Forecast ({year})"
        comparison_scenario = "Forecast"
    else:  # prior_year
        comparison_label = f"Prior Year ({comparison_year})"
        comparison_scenario = "Actual"
    
    # Generate timestamp for report
    gen_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Income Statement Comparison - {entity}</title>
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
            max-width: 1200px;
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
        
        .account-row {{
            border-left: 3px solid transparent;
        }}
        
        .account-row.total-row {{
            border-top: 2px solid #34495e;
            font-weight: bold;
            background-color: #f8f9fa;
        }}
        
        .account-row.subtotal-row {{
            border-top: 1px solid #bdc3c7;
            font-weight: 600;
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
        <h1>📊 Income Statement Comparison Report</h1>
        <div class="subtitle">
            <strong>Entity:</strong> {entity}<br>
            <strong>Period:</strong> {year} {period} (YTD)<br>
            <strong>Comparison:</strong> Actual vs {comparison_label}<br>
            <strong>Generated:</strong> {gen_time}
        </div>"""
    
    html += f"""
        
        <div class="summary-box">
            <h2 style="color: white; border: none; padding: 0; margin: 0 0 15px 0;">Key Metrics</h2>
            <div class="summary-metrics">
"""
    
    # Add key metrics to summary
    actual_revenue = actual_data.get("FCCS_Sales") or 0
    comparison_revenue = comparison_data.get("FCCS_Sales") or 0
    revenue_var = variances["FCCS_Sales"]
    
    actual_net_income = actual_data.get("FCCS_Net Income") or 0
    comparison_net_income = comparison_data.get("FCCS_Net Income") or 0
    net_income_var = variances["FCCS_Net Income"]
    
    html += f"""
                <div class="metric">
                    <div class="metric-label">Actual Revenue</div>
                    <div class="metric-value">${actual_revenue:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">{comparison_label} Revenue</div>
                    <div class="metric-value">${comparison_revenue:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Revenue Variance</div>
                    <div class="metric-value">{format_variance_html(revenue_var)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Actual Net Income</div>
                    <div class="metric-value">${actual_net_income:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">{comparison_label} Net Income</div>
                    <div class="metric-value">${comparison_net_income:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Net Income Variance</div>
                    <div class="metric-value">{format_variance_html(net_income_var)}</div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #ffc107;"></span>
                Highlighted variance (>10% or >$1M)
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #27ae60;"></span>
                Positive variance
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #e74c3c;"></span>
                Negative variance
            </span>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Account</th>
                    <th>Actual ({year})</th>
                    <th>{comparison_label}</th>
                    <th>Variance ($)</th>
                    <th>Variance (%)</th>
                </tr>"""
    
    # Format the remaining placeholders in the table header
    html = html.replace("{year}", year).replace("{comparison_label}", comparison_label)
    
    html += """
            </thead>
            <tbody>
"""
    
    # Add Income Statement rows
    for account_code, account_label in INCOME_STATEMENT_ACCOUNTS:
        actual_value = actual_data.get(account_code)
        comparison_value = comparison_data.get(account_code)
        variance = variances[account_code]
        
        # Determine row class
        row_class = "account-row"
        if account_code == "FCCS_Gross Profit" or account_code == "FCCS_Operating Income":
            row_class += " subtotal-row"
        elif account_code == "FCCS_Net Income":
            row_class += " total-row"
        
        html += f"""
                <tr class="{row_class}">
                    <td><strong>{account_label}</strong></td>
                    <td>{format_value_html(actual_value)}</td>
                    <td>{format_value_html(comparison_value)}</td>
                    <td>{format_variance_amount_html(variance)}</td>
                    <td>{format_variance_percent_html(variance)}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>Report generated by FCCS MCP Agent</p>
            <p>Data source: Oracle FCCS Application</p>
            <p>Note: Variances are calculated as (Actual - Comparison) / |Comparison| × 100%</p>
            <p>Report Timestamp: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def format_value_html(val: Optional[float]) -> str:
    """Format a value for HTML display."""
    if val is None:
        return '<span class="neutral">N/A</span>'
    return f"${val:,.2f}"


def format_variance_amount_html(variance: Dict) -> str:
    """Format variance amount for HTML display."""
    if variance["amount"] is None:
        return '<span class="neutral">N/A</span>'
    
    amount = variance["amount"]
    sign = "+" if amount >= 0 else ""
    class_name = "positive" if amount >= 0 else "negative"
    
    if variance["highlight"]:
        return f'<span class="highlight-variance">{sign}${amount:,.2f}</span>'
    else:
        return f'<span class="{class_name}">{sign}${amount:,.2f}</span>'


def format_variance_percent_html(variance: Dict) -> str:
    """Format variance percentage for HTML display."""
    if variance["percent"] is None:
        return '<span class="neutral">N/A</span>'
    
    percent = variance["percent"]
    sign = "+" if percent >= 0 else ""
    class_name = "positive" if percent >= 0 else "negative"
    
    if variance["highlight"]:
        return f'<span class="highlight-variance">{sign}{percent:.1f}%</span>'
    else:
        return f'<span class="{class_name}">{sign}{percent:.1f}%</span>'


def format_variance_html(variance: Dict) -> str:
    """Format variance for summary display."""
    if variance["amount"] is None:
        return "N/A"
    
    amount = variance["amount"]
    percent = variance["percent"]
    sign = "+" if amount >= 0 else ""
    
    if percent is not None:
        return f"{sign}${amount:,.0f} ({sign}{percent:.1f}%)"
    else:
        return f"{sign}${amount:,.0f}"


async def generate_income_statement_report(
    entity: str = "FCCS_Total Geography",
    year: str = "FY25",
    period: str = "Dec",
    comparison_type: str = "forecast",  # "forecast" or "prior_year"
    comparison_year: str = "FY24"
):
    """Generate Income Statement comparison report."""
    print("=" * 80)
    print("INCOME STATEMENT COMPARISON REPORT")
    print("=" * 80)
    print()
    print(f"Entity: {entity}")
    print(f"Period: {year} {period} (YTD)")
    
    if comparison_type == "forecast":
        print(f"Comparison: Actual vs Forecast ({year})")
    else:
        print(f"Comparison: Actual ({year}) vs Prior Year ({comparison_year})")
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get Actual data
        print("Retrieving Actual data...")
        actual_data = await get_income_statement_data(entity, year, "Actual", period)
        print("[OK] Actual data retrieved")
        print()
        
        # Get Comparison data
        if comparison_type == "forecast":
            print("Retrieving Forecast data...")
            comparison_data = await get_income_statement_data(entity, year, "Forecast", period)
            comp_year = year
        else:  # prior_year
            print(f"Retrieving Prior Year ({comparison_year}) data...")
            comparison_data = await get_income_statement_data(entity, comparison_year, "Actual", period)
            comp_year = comparison_year
        
        print("[OK] Comparison data retrieved")
        print()
        
        # Generate HTML report
        print("Generating HTML report...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        html_content = generate_html_report(
            entity=entity,
            year=year,
            period=period,
            comparison_type=comparison_type,
            comparison_year=comp_year,
            actual_data=actual_data,
            comparison_data=comparison_data,
            timestamp=timestamp
        )
        
        # Save report
        safe_entity = entity.replace(" ", "_").replace("/", "_")
        comparison_suffix = "Forecast" if comparison_type == "forecast" else f"PriorYear_{comparison_year}"
        report_filename = f"Income_Statement_Comparison_{safe_entity}_{year}_{comparison_suffix}_{timestamp}.html"
        report_path = Path(report_filename)
        report_path.write_text(html_content, encoding="utf-8")
        
        print("=" * 80)
        print("REPORT GENERATED")
        print("=" * 80)
        print(f"File: {report_filename}")
        print(f"Path: {report_path.absolute()}")
        print()
        
        # Print summary
        print("Summary:")
        for account_code, account_label in INCOME_STATEMENT_ACCOUNTS:
            actual_val = actual_data.get(account_code)
            comp_val = comparison_data.get(account_code)
            variance = calculate_variance(actual_val, comp_val)
            
            if actual_val is not None and comp_val is not None:
                print(f"  {account_label}:")
                print(f"    Actual: ${actual_val:,.2f}")
                print(f"    Comparison: ${comp_val:,.2f}")
                if variance["amount"] is not None:
                    sign = "+" if variance["amount"] >= 0 else ""
                    pct_str = f" ({variance['percent']:+.1f}%)" if variance["percent"] is not None else ""
                    highlight = " [HIGHLIGHT]" if variance["highlight"] else ""
                    print(f"    Variance: {sign}${variance['amount']:,.2f}{pct_str}{highlight}")
                print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Income Statement Comparison Report")
    parser.add_argument("--entity", default="FCCS_Total Geography", help="Entity name (default: FCCS_Total Geography)")
    parser.add_argument("--year", default="FY25", help="Year (default: FY25)")
    parser.add_argument("--period", default="Dec", help="Period (default: Dec)")
    parser.add_argument("--comparison", choices=["forecast", "prior_year"], default="forecast",
                       help="Comparison type: forecast or prior_year (default: forecast)")
    parser.add_argument("--prior-year", default="FY24", help="Prior year for comparison (default: FY24)")
    
    args = parser.parse_args()
    
    asyncio.run(generate_income_statement_report(
        entity=args.entity,
        year=args.year,
        period=args.period,
        comparison_type=args.comparison,
        comparison_year=args.prior_year
    ))

