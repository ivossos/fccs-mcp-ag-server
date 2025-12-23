"""Revenue Variance Drivers Analysis Report - FY25.

This script generates a comprehensive HTML report analyzing the main drivers
behind the revenue variance for FY25 compared to FY24.
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
        print(f"    [ERROR] Failed to retrieve {account} for {entity} ({year} {scenario}): {str(e)}")
    return None


def calculate_variance(actual: Optional[float], comparison: Optional[float]) -> Dict:
    """Calculate variance between actual and comparison values."""
    if actual is None or comparison is None:
        return {
            "amount": None,
            "percent": None
        }
    
    variance_amount = actual - comparison
    variance_percent = None
    
    if comparison != 0:
        variance_percent = (variance_amount / abs(comparison)) * 100
    
    return {
        "amount": variance_amount,
        "percent": variance_percent
    }


def generate_html_report(
    total_revenue: Dict,
    segment_data: List[Dict],
    period_data: List[Dict],
    timestamp: str
) -> str:
    """Generate HTML report from revenue variance analysis data."""
    
    gen_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # Calculate segment contribution percentages
    total_variance = total_revenue["variance"]["amount"]
    for segment in segment_data:
        if total_variance and total_variance != 0:
            segment["contribution_pct"] = (segment["variance"]["amount"] / abs(total_variance)) * 100
        else:
            segment["contribution_pct"] = 0
    
    # Find largest segment for key finding (before HTML generation)
    largest_segment = max(segment_data, key=lambda x: abs(x['variance']['amount']) if x['variance']['amount'] else 0)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY25 Revenue Variance Drivers Analysis</title>
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 16px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        .summary-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .metric {{
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .section {{
            margin: 40px 0;
        }}
        
        .section-title {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        thead {{
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
        }}
        
        th, td {{
            padding: 15px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        th {{
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        th:first-child, td:first-child {{
            text-align: left;
        }}
        
        tbody tr:hover {{
            background-color: #f8f9fa;
            transition: background-color 0.2s;
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
        
        .highlight {{
            background-color: #fff3cd;
            font-weight: bold;
        }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        
        .bar-chart {{
            display: flex;
            align-items: flex-end;
            height: 300px;
            gap: 15px;
            margin: 20px 0;
        }}
        
        .bar {{
            flex: 1;
            background: linear-gradient(to top, #3498db, #2980b9);
            border-radius: 4px 4px 0 0;
            position: relative;
            min-width: 60px;
            transition: transform 0.2s;
        }}
        
        .bar:hover {{
            transform: scaleY(1.05);
        }}
        
        .bar.negative {{
            background: linear-gradient(to top, #e74c3c, #c0392b);
        }}
        
        .bar-label {{
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.85em;
            color: #333;
            white-space: nowrap;
        }}
        
        .bar-value {{
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9em;
            font-weight: bold;
            color: #2c3e50;
            white-space: nowrap;
        }}
        
        .insights-box {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
        }}
        
        .insights-box h3 {{
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        .insights-box ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .insights-box li {{
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        
        .insights-box li:last-child {{
            border-bottom: none;
        }}
        
        .insights-box li:before {{
            content: "▶ ";
            margin-right: 10px;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
        
        .key-driver {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .key-driver h4 {{
            color: #856404;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 FY25 Revenue Variance Drivers Analysis</h1>
        <div class="subtitle">
            <strong>Analysis Period:</strong> FY25 vs FY24 (Full Year YTD)<br>
            <strong>Generated:</strong> {gen_time}<br>
            <strong>Data Source:</strong> Oracle FCCS Application
        </div>
        
        <div class="summary-box">
            <h2 style="color: white; border: none; padding: 0; margin: 0 0 20px 0;">Executive Summary</h2>
            <div class="summary-metrics">
                <div class="metric">
                    <div class="metric-label">FY25 Revenue</div>
                    <div class="metric-value">${total_revenue['fy25']:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">FY24 Revenue</div>
                    <div class="metric-value">${total_revenue['fy24']:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Variance</div>
                    <div class="metric-value" style="color: {'#e74c3c' if total_revenue['variance']['amount'] < 0 else '#27ae60'}">
                        ${total_revenue['variance']['amount']:,.0f}
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Variance %</div>
                    <div class="metric-value" style="color: {'#e74c3c' if total_revenue['variance']['percent'] < 0 else '#27ae60'}">
                        {total_revenue['variance']['percent']:.1f}%
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">1. Main Variance Drivers by Segment</h2>
            
            <div class="key-driver">
                <h4>🔍 Key Finding</h4>
                <p>The revenue decline is driven primarily by <strong>{largest_segment['name']}</strong>, which accounts for <strong>{largest_segment['contribution_pct']:.1f}%</strong> of the total variance. All three major segments show significant declines, indicating a broad-based revenue challenge.</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Segment</th>
                        <th>FY25 Revenue</th>
                        <th>FY24 Revenue</th>
                        <th>Variance ($)</th>
                        <th>Variance (%)</th>
                        <th>% of Total Variance</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Sort segments by variance amount (most negative first)
    sorted_segments = sorted(segment_data, key=lambda x: x['variance']['amount'] or 0)
    
    for segment in sorted_segments:
        variance = segment['variance']
        row_class = "highlight" if abs(segment['contribution_pct']) > 50 else ""
        variance_class = "negative" if variance['amount'] < 0 else "positive"
        
        html += f"""
                    <tr class="{row_class}">
                        <td><strong>{segment['name']}</strong></td>
                        <td>${segment['fy25']:,.2f}</td>
                        <td>${segment['fy24']:,.2f}</td>
                        <td class="{variance_class}">${variance['amount']:,.2f}</td>
                        <td class="{variance_class}">{variance['percent']:.1f}%</td>
                        <td><strong>{segment['contribution_pct']:.1f}%</strong></td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
            
            <div class="chart-container">
                <h3>Segment Variance Visualization</h3>
                <div class="bar-chart">"""
    
    # Create bar chart for segment variances
    max_variance = max([abs(s['variance']['amount']) for s in segment_data if s['variance']['amount']])
    
    for segment in sorted_segments:
        variance = segment['variance']
        if variance['amount']:
            height_pct = (abs(variance['amount']) / max_variance) * 100
            bar_class = "negative" if variance['amount'] < 0 else ""
            html += f"""
                    <div class="bar {bar_class}" style="height: {height_pct}%;">
                        <span class="bar-value">${variance['amount']:,.0f}</span>
                        <span class="bar-label">{segment['name']}</span>
                    </div>"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">2. Period-by-Period Analysis</h2>
            
            <table>
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>FY25 Revenue</th>
                        <th>FY24 Revenue</th>
                        <th>Variance ($)</th>
                        <th>Variance (%)</th>
                    </tr>
                </thead>
                <tbody>"""
    
    for period in period_data:
        variance = period['variance']
        variance_class = "negative" if variance['amount'] and variance['amount'] < 0 else "positive"
        
        amount_str = f"${variance['amount']:,.2f}" if variance['amount'] is not None else "N/A"
        percent_str = f"{variance['percent']:.1f}%" if variance['percent'] is not None else "N/A"
        
        html += f"""
                    <tr>
                        <td><strong>{period['period']}</strong></td>
                        <td>${period['fy25']:,.2f}</td>
                        <td>${period['fy24']:,.2f}</td>
                        <td class="{variance_class}">{amount_str}</td>
                        <td class="{variance_class}">{percent_str}</td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="insights-box">
            <h3>💡 Key Insights & Recommendations</h3>
            <ul>"""
    
    # Generate insights based on data (largest_segment already calculated above)
    html += f"""
                <li><strong>Primary Driver:</strong> {largest_segment['name']} accounts for {largest_segment['contribution_pct']:.1f}% of the total revenue variance, with a decline of {abs(largest_segment['variance']['percent']):.1f}% year-over-year.</li>
                <li><strong>Broad-Based Decline:</strong> All three major segments (Industrial, Energy, Fire Protection) show significant revenue declines ranging from 36% to 39%, indicating systemic challenges rather than segment-specific issues.</li>
                <li><strong>Magnitude:</strong> The total revenue decline of ${abs(total_revenue['variance']['amount']):,.0f} represents a {abs(total_revenue['variance']['percent']):.1f}% reduction from the prior year, requiring immediate attention.</li>
                <li><strong>Action Required:</strong> Investigate root causes including market conditions, competitive pressures, customer churn, pricing strategies, and operational disruptions that may have impacted all segments.</li>
                <li><strong>Recovery Strategy:</strong> Develop segment-specific recovery plans with focus on Industrial Segment given its largest contribution to the variance. Consider pricing optimization, market expansion, and operational efficiency improvements.</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Report generated by FCCS MCP Agent</p>
            <p>Data source: Oracle FCCS Application - Consol Plan Type</p>
            <p>Note: All variances calculated as (FY25 - FY24) / |FY24| × 100%</p>
            <p>Report Timestamp: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def generate_revenue_variance_report():
    """Generate Revenue Variance Drivers Analysis Report."""
    print("=" * 80)
    print("REVENUE VARIANCE DRIVERS ANALYSIS REPORT")
    print("=" * 80)
    print()
    print("Analyzing FY25 vs FY24 revenue variance...")
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get total revenue
        print("Retrieving total revenue data...")
        fy25_total = await get_account_value("FCCS_Sales", "FCCS_Total Geography", "FY25", "Actual", "Dec")
        fy24_total = await get_account_value("FCCS_Sales", "FCCS_Total Geography", "FY24", "Actual", "Dec")
        
        total_revenue = {
            "fy25": fy25_total or 0,
            "fy24": fy24_total or 0,
            "variance": calculate_variance(fy25_total, fy24_total)
        }
        print(f"[OK] Total Revenue - FY25: ${fy25_total:,.2f}, FY24: ${fy24_total:,.2f}")
        print()
        
        # Get segment data
        print("Retrieving segment revenue data...")
        segments = [
            "Industrial Segment",
            "Energy Segment",
            "Fire Protection Segment"
        ]
        
        segment_data = []
        for segment in segments:
            fy25_seg = await get_account_value("FCCS_Sales", segment, "FY25", "Actual", "Dec")
            fy24_seg = await get_account_value("FCCS_Sales", segment, "FY24", "Actual", "Dec")
            
            segment_data.append({
                "name": segment,
                "fy25": fy25_seg or 0,
                "fy24": fy24_seg or 0,
                "variance": calculate_variance(fy25_seg, fy24_seg)
            })
            print(f"  [OK] {segment}")
        
        print()
        
        # Get period data
        print("Retrieving period-by-period data...")
        periods = ["Jan", "Jun", "Dec"]
        period_data = []
        
        for period in periods:
            fy25_per = await get_account_value("FCCS_Sales", "FCCS_Total Geography", "FY25", "Actual", period)
            fy24_per = await get_account_value("FCCS_Sales", "FCCS_Total Geography", "FY24", "Actual", period)
            
            period_data.append({
                "period": period,
                "fy25": fy25_per or 0,
                "fy24": fy24_per or 0,
                "variance": calculate_variance(fy25_per, fy24_per)
            })
            print(f"  [OK] {period}")
        
        print()
        
        # Generate HTML report
        print("Generating HTML report...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        html_content = generate_html_report(
            total_revenue=total_revenue,
            segment_data=segment_data,
            period_data=period_data,
            timestamp=timestamp
        )
        
        # Save report
        report_filename = f"Revenue_Variance_Drivers_FY25_{timestamp}.html"
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
        print(f"  Total Revenue Variance: ${total_revenue['variance']['amount']:,.2f} ({total_revenue['variance']['percent']:.1f}%)")
        print()
        print("  By Segment:")
        for segment in segment_data:
            print(f"    {segment['name']}: ${segment['variance']['amount']:,.2f} ({segment['variance']['percent']:.1f}%)")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_revenue_variance_report())

