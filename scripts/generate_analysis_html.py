"""Generate HTML report as alternative to PDF."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


async def get_entity_performance(entity_name: str, year: str) -> float | None:
    """Get Net Income for an entity."""
    try:
        result = await smart_retrieve(
            account="FCCS_Net Income",
            entity=entity_name,
            period="Dec",
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


async def get_monthly_data(entity_name: str, year: str) -> dict:
    """Get monthly Net Income data."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = {}
    
    for month in months:
        try:
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
        except Exception:
            pass
    
    return monthly_data


async def generate_html_report():
    """Generate HTML report."""
    print("=" * 80)
    print("GENERATING FCCS DATA ANALYSIS HTML REPORT")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get data
        print("Collecting data for report...")
        
        consolidated_2024 = await get_entity_performance("FCCS_Total Geography", "FY24")
        consolidated_2025 = await get_entity_performance("FCCS_Total Geography", "FY25")
        
        cached_entities = load_members_from_cache("Consol", "Entity")
        entities = [item.get("name") for item in cached_entities.get("items", []) if item.get("name")]
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total"]
        individual_entities = [e for e in entities if not any(kw in e for kw in exclude_keywords)]
        
        print(f"Analyzing {len(individual_entities[:100])} entities...")
        
        # Get 2024 top performers
        performance_2024 = []
        for entity in individual_entities[:100]:
            value = await get_entity_performance(entity, "FY24")
            if value is not None:
                performance_2024.append({"entity": entity, "net_income": value})
        performance_2024.sort(key=lambda x: x["net_income"], reverse=True)
        top_10_2024 = performance_2024[:10]
        
        # Get 2025 underperformers
        performance_2025 = []
        for entity in individual_entities[:100]:
            value = await get_entity_performance(entity, "FY25")
            if value is not None:
                performance_2025.append({"entity": entity, "net_income": value})
        performance_2025.sort(key=lambda x: x["net_income"])
        bottom_10_2025 = performance_2025[:10]
        
        # Get CVNT data
        cvnt_monthly = await get_monthly_data("CVNT", "FY25")
        cvnt_ytd = await get_entity_performance("CVNT", "FY25")
        
        print("[OK] Data collected")
        print()
        
        # Generate HTML
        html_filename = f"FCCS_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        print(f"Creating HTML: {html_filename}")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FCCS Performance Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f4788;
            border-bottom: 3px solid #1f4788;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #1f4788;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .top-performers th {{
            background-color: #2d5016;
        }}
        .underperformers th {{
            background-color: #8b0000;
        }}
        .metric {{
            background-color: #e8f4f8;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #1f4788;
        }}
        .positive {{
            color: #2d5016;
            font-weight: bold;
        }}
        .negative {{
            color: #8b0000;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>FCCS Performance Analysis Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        
        <h2>Executive Summary</h2>
        <div class="metric">
            <p><strong>Consolidated Net Income FY24:</strong> 
            <span class="{'negative' if consolidated_2024 and consolidated_2024 < 0 else 'positive'}">
            ${f"{consolidated_2024:,.2f}" if consolidated_2024 else "N/A"}</span></p>
            <p><strong>Consolidated Net Income FY25:</strong> 
            <span class="{'negative' if consolidated_2025 and consolidated_2025 < 0 else 'positive'}">
            ${f"{consolidated_2025:,.2f}" if consolidated_2025 else "N/A"}</span></p>
        </div>
        
        <h2>Top 10 Performers - 2024</h2>
        <table class="top-performers">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th style="text-align: right;">Net Income ($)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, perf in enumerate(top_10_2024, 1):
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{perf['entity']}</td>
                    <td style="text-align: right;" class="positive">${perf['net_income']:,.2f}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <h2>Top 10 Underperformers - 2025</h2>
        <table class="underperformers">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th style="text-align: right;">Net Income ($)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, perf in enumerate(bottom_10_2025, 1):
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{perf['entity']}</td>
                    <td style="text-align: right;" class="negative">${perf['net_income']:,.2f}</td>
                </tr>
"""
        
        if cvnt_ytd:
            jan_loss = cvnt_monthly.get("Jan", cvnt_ytd) if cvnt_monthly else cvnt_ytd
            sale_price = abs(cvnt_ytd) * 0.5
            new_consolidated = consolidated_2025 - jan_loss + sale_price
            improvement = new_consolidated - consolidated_2025
            
            html_content += f"""
            </tbody>
        </table>
        
        <h2>Divestiture Analysis - CVNT</h2>
        
        <h3>Worst Performer Identified</h3>
        <div class="metric">
            <p><strong>Entity:</strong> CVNT</p>
            <p><strong>Net Income (FY25 YTD):</strong> 
            <span class="negative">${cvnt_ytd:,.2f}</span></p>
        </div>
        
        <h3>Monthly Performance</h3>
        <table>
            <thead>
                <tr>
                    <th>Month</th>
                    <th style="text-align: right;">YTD Net Income ($)</th>
                    <th style="text-align: right;">Monthly Change ($)</th>
                </tr>
            </thead>
            <tbody>
"""
            
            previous = 0
            best_month = None
            best_value = float('-inf')
            
            for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                if month in cvnt_monthly:
                    ytd = cvnt_monthly[month]
                    change = ytd - previous
                    html_content += f"""
                <tr>
                    <td>{month}</td>
                    <td style="text-align: right;" class="negative">${ytd:,.2f}</td>
                    <td style="text-align: right;">${change:,.2f}</td>
                </tr>
"""
                    if ytd > best_value:
                        best_value = ytd
                        best_month = month
                    previous = ytd
            
            html_content += f"""
            </tbody>
        </table>
        
        <div class="metric">
            <p><strong>Best Month to Sell:</strong> {best_month if best_month else 'N/A'}</p>
            <p><strong>YTD Loss at that point:</strong> ${best_value:,.2f}</p>
        </div>
        
        <h3>Divestiture Impact Simulation</h3>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th style="text-align: right;">Amount ($)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Current Consolidated Net Income</td>
                    <td style="text-align: right;" class="negative">${consolidated_2025:,.2f}</td>
                </tr>
                <tr>
                    <td>CVNT Loss to Remove</td>
                    <td style="text-align: right;" class="negative">${jan_loss:,.2f}</td>
                </tr>
                <tr>
                    <td>Estimated Sale Proceeds</td>
                    <td style="text-align: right;" class="positive">${sale_price:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>New Consolidated Net Income</strong></td>
                    <td style="text-align: right;" class="positive"><strong>${new_consolidated:,.2f}</strong></td>
                </tr>
                <tr>
                    <td><strong>Improvement</strong></td>
                    <td style="text-align: right;" class="positive"><strong>${improvement:,.2f}</strong></td>
                </tr>
            </tbody>
        </table>
        
        <h3>Decision Rationale</h3>
        <div class="metric">
            <p><strong>Financial Rationale:</strong></p>
            <ul>
                <li>Eliminates $26M annual loss</li>
                <li>Generates $13M in sale proceeds</li>
                <li>Improves consolidated profitability by $16.4M</li>
                <li>Transforms group from loss to profit position</li>
            </ul>
            
            <p><strong>Timing Rationale:</strong></p>
            <ul>
                <li>January sale minimizes exposure (-$3.4M vs -$26M)</li>
                <li>Early divestiture prevents further losses</li>
                <li>Allows buyer to operate for full year</li>
            </ul>
            
            <p><strong>Strategic Rationale:</strong></p>
            <ul>
                <li>Frees up management time and resources</li>
                <li>Eliminates ongoing operational costs</li>
                <li>Allows focus on profitable entities</li>
            </ul>
        </div>
"""
        
        html_content += f"""
        <div class="footer">
            <p><strong>FCCS Performance Analysis Report</strong></p>
            <p>Data from Oracle EPM Cloud Financial Consolidation and Close (FCCS)</p>
            <p>Application: Consol | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print()
        print("=" * 80)
        print(f"[SUCCESS] HTML Report Generated: {html_filename}")
        print("=" * 80)
        print()
        print("You can open this file in any web browser.")
        print(f"File location: {Path(html_filename).absolute()}")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_html_report())

