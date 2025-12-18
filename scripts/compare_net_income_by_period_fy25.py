"""Compare Net Income for an Entity across all periods in FY25 and identify best/worst months.

This script:
1. Retrieves Net Income for all 12 months in FY25 for a specific entity
2. Identifies the best and worst performing months
3. Generates an HTML report with analysis
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


async def get_monthly_net_income(entity_name: str, year: str = "FY25") -> Dict[str, float]:
    """Get monthly Net Income data for all 12 months."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = {}
    
    print(f"Retrieving Net Income for {entity_name} across all periods in {year}...")
    print()
    
    for idx, month in enumerate(months, 1):
        try:
            print(f"  [{idx}/12] Retrieving {month}...", end=" ", flush=True)
            result = await smart_retrieve(
                account="FCCS_Net Income",
                entity=entity_name,
                period=month,
                years=year,
                scenario="Actual"
            )
            if result.get("status") == "success":
                data = result.get("data", {})
                rows = data.get("rows", [])
                if rows and rows[0].get("data"):
                    value = rows[0]["data"][0]
                    if value is not None:
                        monthly_data[month] = float(value)
                        print(f"${float(value):,.2f}")
                    else:
                        print("No data")
                else:
                    print("No data")
            else:
                print("Error")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    return monthly_data


def analyze_performance(monthly_data: Dict[str, float]) -> Dict:
    """Analyze monthly performance and identify best/worst months."""
    if not monthly_data:
        return {
            "best_month": None,
            "worst_month": None,
            "best_value": None,
            "worst_value": None,
            "average": None,
            "total": None,
            "monthly_changes": {},
            "trend": None
        }
    
    # Find best and worst months
    best_month = max(monthly_data.items(), key=lambda x: x[1])
    worst_month = min(monthly_data.items(), key=lambda x: x[1])
    
    # Calculate statistics
    values = list(monthly_data.values())
    average = sum(values) / len(values) if values else 0
    total = sum(values)
    
    # Calculate month-over-month changes
    monthly_changes = {}
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    prev_value = None
    for month in months_order:
        if month in monthly_data:
            current_value = monthly_data[month]
            if prev_value is not None:
                change = current_value - prev_value
                change_pct = (change / abs(prev_value) * 100) if prev_value != 0 else 0
                monthly_changes[month] = {
                    "change": change,
                    "change_pct": change_pct
                }
            prev_value = current_value
    
    # Determine trend (improving, declining, or mixed)
    if len(values) >= 3:
        first_quarter_avg = sum([monthly_data.get(m, 0) for m in months_order[:3] if m in monthly_data]) / 3
        last_quarter_avg = sum([monthly_data.get(m, 0) for m in months_order[-3:] if m in monthly_data]) / 3
        if last_quarter_avg > first_quarter_avg * 1.1:
            trend = "Improving"
        elif last_quarter_avg < first_quarter_avg * 0.9:
            trend = "Declining"
        else:
            trend = "Stable"
    else:
        trend = "Insufficient data"
    
    return {
        "best_month": best_month[0],
        "worst_month": worst_month[0],
        "best_value": best_month[1],
        "worst_value": worst_month[1],
        "average": average,
        "total": total,
        "monthly_changes": monthly_changes,
        "trend": trend,
        "spread": best_month[1] - worst_month[1]
    }


def generate_html_report(
    entity_name: str,
    year: str,
    monthly_data: Dict[str, float],
    analysis: Dict
) -> str:
    """Generate HTML report for Net Income comparison across periods."""
    
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Build monthly data table rows
    monthly_rows = ""
    for month in months_order:
        if month in monthly_data:
            value = monthly_data[month]
            change_info = analysis["monthly_changes"].get(month, {})
            change = change_info.get("change", 0)
            change_pct = change_info.get("change_pct", 0)
            
            # Highlight best and worst months
            row_class = ""
            if month == analysis["best_month"]:
                row_class = "best-month"
            elif month == analysis["worst_month"]:
                row_class = "worst-month"
            
            change_class = "positive" if change >= 0 else "negative"
            change_sign = "+" if change >= 0 else ""
            
            monthly_rows += f"""
                        <tr class="{row_class}">
                            <td><strong>{month}</strong></td>
                            <td class="value">${value:,.2f}</td>
                            <td class="change {change_class}">{change_sign}${change:,.2f}</td>
                            <td class="change {change_class}">{change_sign}{change_pct:.1f}%</td>
                        </tr>
"""
        else:
            monthly_rows += f"""
                        <tr>
                            <td>{month}</td>
                            <td colspan="3" class="no-data">No data available</td>
                        </tr>
"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Net Income Period Comparison - {entity_name} {year}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .summary-card.highlight-best {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
        }}
        
        .summary-card.highlight-worst {{
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 2px solid #dc3545;
        }}
        
        .summary-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .summary-card .value.positive {{
            color: #28a745;
        }}
        
        .summary-card .value.negative {{
            color: #dc3545;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 0.95em;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr.best-month {{
            background: #d4edda;
            font-weight: 600;
        }}
        
        tr.worst-month {{
            background: #f8d7da;
            font-weight: 600;
        }}
        
        .value {{
            font-weight: 600;
            color: #495057;
        }}
        
        .change.positive {{
            color: #28a745;
            font-weight: 600;
        }}
        
        .change.negative {{
            color: #dc3545;
            font-weight: 600;
        }}
        
        .no-data {{
            color: #6c757d;
            font-style: italic;
        }}
        
        .insights {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
        }}
        
        .insights h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .insights ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .insights li {{
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .insights li:last-child {{
            border-bottom: none;
        }}
        
        .insights li::before {{
            content: "• ";
            color: #667eea;
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Net Income Period Comparison</h1>
            <p>{entity_name} - {year}</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <div class="summary-card highlight-best">
                    <h3>🏆 Best Performing Month</h3>
                    <div class="value positive">{analysis['best_month']}</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">
                        ${analysis['best_value']:,.2f}
                    </div>
                </div>
                <div class="summary-card highlight-worst">
                    <h3>⚠️ Worst Performing Month</h3>
                    <div class="value negative">{analysis['worst_month']}</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">
                        ${analysis['worst_value']:,.2f}
                    </div>
                </div>
                <div class="summary-card">
                    <h3>📈 Average Monthly</h3>
                    <div class="value">${analysis['average']:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>💰 Total {year}</h3>
                    <div class="value">${analysis['total']:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>📊 Performance Spread</h3>
                    <div class="value">${analysis['spread']:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>📉 Trend</h3>
                    <div class="value">{analysis['trend']}</div>
                </div>
            </div>
            
            <div class="insights">
                <h3>Key Insights</h3>
                <ul>
                    <li><strong>Best Month:</strong> {analysis['best_month']} with Net Income of ${analysis['best_value']:,.2f}</li>
                    <li><strong>Worst Month:</strong> {analysis['worst_month']} with Net Income of ${analysis['worst_value']:,.2f}</li>
                    <li><strong>Performance Gap:</strong> ${analysis['spread']:,.2f} difference between best and worst months</li>
                    <li><strong>Average Performance:</strong> ${analysis['average']:,.2f} per month</li>
                    <li><strong>Overall Trend:</strong> {analysis['trend']}</li>
                    <li><strong>Total {year} Net Income:</strong> ${analysis['total']:,.2f}</li>
                </ul>
            </div>
            
            <div class="section">
                <div class="section-header">📅 Monthly Net Income Breakdown</div>
                <table>
                    <thead>
                        <tr>
                            <th>Period</th>
                            <th>Net Income</th>
                            <th>MoM Change ($)</th>
                            <th>MoM Change (%)</th>
                        </tr>
                    </thead>
                    <tbody>
{monthly_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def compare_net_income_by_period(entity_name: str = "FCCS_Total Geography", year: str = "FY25"):
    """Compare Net Income for an entity across all periods in FY25."""
    print("=" * 80)
    print(f"NET INCOME PERIOD COMPARISON - {entity_name}")
    print(f"Year: {year}")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get monthly data
        monthly_data = await get_monthly_net_income(entity_name, year)
        
        if not monthly_data:
            print("[ERROR] No data found for any period")
            print("Please verify:")
            print(f"  • Entity name '{entity_name}' is correct")
            print(f"  • Data has been loaded for {year}")
            print("  • Account 'FCCS_Net Income' exists and has data")
            await close_agent()
            return
        
        print()
        print(f"[OK] Retrieved data for {len(monthly_data)} periods")
        print()
        
        # Analyze performance
        print("Analyzing performance...")
        analysis = analyze_performance(monthly_data)
        print("[OK] Analysis complete")
        print()
        
        # Print summary to console
        print("=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        print()
        print(f"Best Performing Month:  {analysis['best_month']:>3} - ${analysis['best_value']:>15,.2f}")
        print(f"Worst Performing Month: {analysis['worst_month']:>3} - ${analysis['worst_value']:>15,.2f}")
        print(f"Performance Spread:     ${analysis['spread']:>15,.2f}")
        print(f"Average Monthly:        ${analysis['average']:>15,.2f}")
        print(f"Total {year}:              ${analysis['total']:>15,.2f}")
        print(f"Overall Trend:          {analysis['trend']}")
        print()
        
        # Print monthly breakdown
        print("=" * 80)
        print("MONTHLY BREAKDOWN")
        print("=" * 80)
        print()
        print(f"{'Period':<8} {'Net Income':>20} {'MoM Change':>15} {'MoM Change %':>15}")
        print("-" * 80)
        
        months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        for month in months_order:
            if month in monthly_data:
                value = monthly_data[month]
                change_info = analysis["monthly_changes"].get(month, {})
                change = change_info.get("change", 0)
                change_pct = change_info.get("change_pct", 0)
                
                marker = " [BEST]" if month == analysis["best_month"] else " [WORST]" if month == analysis["worst_month"] else ""
                change_sign = "+" if change >= 0 else ""
                
                print(f"{month:<8} ${value:>19,.2f} {change_sign}${change:>14,.2f} {change_sign}{change_pct:>14.1f}%{marker}")
            else:
                print(f"{month:<8} {'No data':>20}")
        
        print()
        
        # Generate HTML report
        print("Generating HTML report...")
        html_content = generate_html_report(entity_name, year, monthly_data, analysis)
        
        # Save HTML file
        project_root = Path(__file__).parent.parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_entity = entity_name.replace(" ", "_").replace("/", "_")
        filename = f"Net_Income_Period_Comparison_{safe_entity}_{year}_{timestamp}.html"
        filepath = project_root / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[OK] Report saved to: {filename}")
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    # Accept entity name as command-line argument, or use default
    entity_name = sys.argv[1] if len(sys.argv) > 1 else "FCCS_Total Geography"
    asyncio.run(compare_net_income_by_period(entity_name))

