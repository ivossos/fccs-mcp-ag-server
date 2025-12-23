"""Generate HTML report for Comprehensive Entity Analysis 2024."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.application import get_application_info
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


async def query_entity_performance(entity_name: str, year: str = "FY24") -> Optional[float]:
    """Query Net Income for a specific entity."""
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


async def get_entity_balance_sheet(entity_name: str, year: str = "FY24") -> dict:
    """Get key balance sheet items for an entity."""
    accounts = {
        "Total Assets": "FCCS_Total Assets",
        "Total Liabilities": "FCCS_Total Liabilities",
        "Total Equity": "FCCS_Total Equity",
        "Sales": "FCCS_Sales"
    }
    
    results = {}
    for label, account in accounts.items():
        try:
            result = await smart_retrieve(
                account=account,
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
                    results[label] = float(value) if value is not None else 0.0
                else:
                    results[label] = 0.0
            else:
                results[label] = 0.0
        except Exception:
            results[label] = 0.0
    
    return results


def generate_html_report(
    apps: list,
    top_10_performers: list,
    bottom_10_performers: list,
    worst_entity: dict,
    worst_entity_financials: dict,
    consolidated_net_income: Optional[float],
    consolidated_sales: float,
    projected_impact: dict
) -> str:
    """Generate HTML report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Entity Analysis - 2024</title>
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
            line-height: 1.6;
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
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .info-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .info-box h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #e8e9ff;
        }}
        .positive {{
            color: #28a745;
            font-weight: 600;
        }}
        .negative {{
            color: #dc3545;
            font-weight: 600;
        }}
        .highlight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .highlight-box h3 {{
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .impact-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .impact-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .impact-card h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
        @media (max-width: 768px) {{
            .impact-section {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Comprehensive Entity Analysis</h1>
            <p>FCCS Financial Performance Report - 2024 Actuals</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </div>
        
        <div class="content">
            <!-- Step 1: Applications -->
            <div class="section">
                <h2 class="section-title">1. FCCS Applications</h2>
                <div class="info-box">
                    <h3>Connected Applications</h3>
                    <p>Found <strong>{len(apps)}</strong> FCCS application(s):</p>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        {''.join([f'<li><strong>{app.get("name")}</strong> (Type: {app.get("appType")})</li>' for app in apps])}
                    </ul>
                </div>
            </div>
            
            <!-- Step 2: Connection -->
            <div class="section">
                <h2 class="section-title">2. Connection Status</h2>
                <div class="info-box">
                    <h3>✅ Successfully Connected</h3>
                    <p>Connected to <strong>Consol</strong> application</p>
                </div>
            </div>
            
            <!-- Step 3: Top Performers -->
            <div class="section">
                <h2 class="section-title">3. Top 10 Performing Entities - 2024</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Entity</th>
                            <th style="text-align: right;">Net Income</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{i}</td>
                            <td>{perf["entity"]}</td>
                            <td style="text-align: right;" class="positive">${perf["net_income"]:,.2f}</td>
                        </tr>
                        ''' for i, perf in enumerate(top_10_performers, 1)])}
                    </tbody>
                </table>
            </div>
            
            <!-- Step 4: Underperformers -->
            <div class="section">
                <h2 class="section-title">4. Top 10 Underperforming Entities - 2024</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Entity</th>
                            <th style="text-align: right;">Net Income</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{i}</td>
                            <td>{perf["entity"]}</td>
                            <td style="text-align: right;" class="negative">${perf["net_income"]:,.2f}</td>
                        </tr>
                        ''' for i, perf in enumerate(bottom_10_performers, 1)])}
                    </tbody>
                </table>
            </div>
            
            <!-- Step 5: Divestment Simulation -->
            <div class="section">
                <h2 class="section-title">5. Divestment Simulation</h2>
                <div class="highlight-box">
                    <h3>🎯 Target Entity for Divestment</h3>
                    <div class="metric">
                        <div class="metric-value">{worst_entity["entity"]}</div>
                        <div class="metric-label">Worst Performing Entity</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${worst_entity["net_income"]:,.2f}</div>
                        <div class="metric-label">2024 Net Income</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">June 30, 2025</div>
                        <div class="metric-label">Divestment Date</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 30px; color: #333;">Financial Details</h3>
                <div class="impact-section">
                    <div class="impact-card">
                        <h4>Total Assets</h4>
                        <p style="font-size: 1.5em; font-weight: bold; color: #667eea;">
                            ${worst_entity_financials.get('Total Assets', 0):,.2f}
                        </p>
                    </div>
                    <div class="impact-card">
                        <h4>Total Liabilities</h4>
                        <p style="font-size: 1.5em; font-weight: bold; color: #667eea;">
                            ${worst_entity_financials.get('Total Liabilities', 0):,.2f}
                        </p>
                    </div>
                    <div class="impact-card">
                        <h4>Total Equity</h4>
                        <p style="font-size: 1.5em; font-weight: bold; color: #667eea;">
                            ${worst_entity_financials.get('Total Equity', 0):,.2f}
                        </p>
                    </div>
                    <div class="impact-card">
                        <h4>Sales</h4>
                        <p style="font-size: 1.5em; font-weight: bold; color: #667eea;">
                            ${worst_entity_financials.get('Sales', 0):,.2f}
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Step 6: Impact Analysis -->
            <div class="section">
                <h2 class="section-title">6. Impact Analysis - Consolidated Group</h2>
                
                <h3 style="margin-top: 20px; color: #333;">Before Divestment (2024 Actuals)</h3>
                <div class="impact-section">
                    <div class="impact-card">
                        <h4>Consolidated Net Income</h4>
                        <p style="font-size: 1.8em; font-weight: bold; color: {'#dc3545' if consolidated_net_income and consolidated_net_income < 0 else '#28a745'};">
                            ${f'{consolidated_net_income:,.2f}' if consolidated_net_income is not None else 'N/A'}
                        </p>
                    </div>
                    <div class="impact-card">
                        <h4>Consolidated Sales</h4>
                        <p style="font-size: 1.8em; font-weight: bold; color: #667eea;">
                            ${consolidated_sales:,.2f}
                        </p>
                    </div>
                </div>
                
                <h3 style="margin-top: 30px; color: #333;">Projected Impact (2025 - 6 Months)</h3>
                <div class="highlight-box">
                    <h3>📉 Impact Metrics</h3>
                    <div class="metric">
                        <div class="metric-value">${projected_impact.get('net_income_impact', 0):,.2f}</div>
                        <div class="metric-label">Net Income Impact</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{projected_impact.get('net_income_impact_pct', 0):.2f}%</div>
                        <div class="metric-label">% of Consolidated NI</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${projected_impact.get('sales_impact', 0):,.2f}</div>
                        <div class="metric-label">Sales Impact</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{projected_impact.get('sales_impact_pct', 0):.2f}%</div>
                        <div class="metric-label">% of Consolidated Sales</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 30px; color: #333;">After Divestment (Projected 2025)</h3>
                <div class="impact-section">
                    <div class="impact-card">
                        <h4>Projected Net Income</h4>
                        <p style="font-size: 1.8em; font-weight: bold; color: {'#dc3545' if projected_impact.get('projected_consolidated_net_income', 0) < 0 else '#28a745'};">
                            ${projected_impact.get('projected_consolidated_net_income', 0):,.2f}
                        </p>
                    </div>
                    <div class="impact-card">
                        <h4>Projected Sales</h4>
                        <p style="font-size: 1.8em; font-weight: bold; color: #667eea;">
                            ${projected_impact.get('projected_consolidated_sales', 0):,.2f}
                        </p>
                    </div>
                </div>
                
                <div class="info-box" style="margin-top: 30px; background: #e8f5e9; border-left-color: #28a745;">
                    <h3 style="color: #28a745;">✅ Key Insight</h3>
                    <p style="font-size: 1.1em; margin-top: 10px;">
                        Divesting <strong>{worst_entity["entity"]}</strong> would {'improve' if projected_impact.get('projected_consolidated_net_income', 0) > (consolidated_net_income or 0) else 'impact'} 
                        consolidated net income by removing a significant loss contributor. 
                        The projected impact shows a {'positive' if projected_impact.get('projected_consolidated_net_income', 0) > (consolidated_net_income or 0) else 'negative'} 
                        change of {projected_impact.get('net_income_impact_pct', 0):.2f}% of current consolidated net income.
                    </p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by FCCS Analysis Tool | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


async def main():
    """Main analysis function."""
    print("=" * 80)
    print("COMPREHENSIVE ENTITY ANALYSIS - 2024 (HTML REPORT)")
    print("=" * 80)
    print()
    
    try:
        # Step 1: List all FCCS apps
        print("Step 1: Listing all FCCS applications...")
        config = load_config()
        await initialize_agent(config)
        
        app_info = await get_application_info()
        if app_info.get("status") != "success":
            print("[ERROR] Could not retrieve application info")
            return
        
        apps = app_info.get("data", {}).get("items", [])
        print(f"[OK] Found {len(apps)} FCCS application(s)")
        
        # Get entities from cache
        print("\nStep 2: Loading entities...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        if cached_entities and cached_entities.get("items"):
            entities_to_query = [item.get("name") for item in cached_entities["items"] if item.get("name")]
            print(f"[OK] Found {len(entities_to_query)} entities to analyze")
        else:
            print("[WARNING] No entity list available")
            await close_agent()
            return
        
        # Query entity performance
        print(f"\nStep 3: Querying Net Income for {len(entities_to_query)} entities...")
        entity_performance = []
        queried = 0
        
        for entity in entities_to_query:
            queried += 1
            if queried % 20 == 0:
                print(f"  Progress: {queried}/{len(entities_to_query)}...")
            
            net_income = await query_entity_performance(entity, "FY24")
            if net_income is not None:
                entity_performance.append({
                    "entity": entity,
                    "net_income": net_income
                })
        
        print(f"[OK] Retrieved performance data for {len(entity_performance)} entities")
        
        # Sort by Net Income
        entity_performance.sort(key=lambda x: x["net_income"], reverse=True)
        top_10_performers = entity_performance[:10]
        entity_performance.sort(key=lambda x: x["net_income"])
        bottom_10_performers = entity_performance[:10]
        
        # Get worst entity details
        worst_entity = bottom_10_performers[0]
        print(f"\nStep 4: Getting financial details for {worst_entity['entity']}...")
        worst_entity_financials = await get_entity_balance_sheet(worst_entity["entity"], "FY24")
        
        # Get consolidated totals
        print("\nStep 5: Getting consolidated group totals...")
        consolidated_net_income = await query_entity_performance("FCCS_Total Geography", "FY24")
        consolidated_sales_result = await smart_retrieve(
            account="FCCS_Sales",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        consolidated_sales = 0.0
        if consolidated_sales_result.get("status") == "success":
            data = consolidated_sales_result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                consolidated_sales = float(value) if value is not None else 0.0
        
        # Calculate projected impact
        projected_2025_net_income = worst_entity["net_income"] * 0.5
        projected_2025_sales = worst_entity_financials.get('Sales', 0) * 0.5
        
        net_income_impact_pct = 0.0
        sales_impact_pct = 0.0
        if consolidated_net_income and consolidated_net_income != 0:
            net_income_impact_pct = (projected_2025_net_income / consolidated_net_income * 100)
        if consolidated_sales != 0:
            sales_impact_pct = (projected_2025_sales / consolidated_sales * 100)
        
        projected_consolidated_net_income_2025 = (consolidated_net_income or 0) - projected_2025_net_income
        projected_consolidated_sales_2025 = consolidated_sales - projected_2025_sales
        
        projected_impact = {
            "net_income_impact": projected_2025_net_income,
            "net_income_impact_pct": net_income_impact_pct,
            "sales_impact": projected_2025_sales,
            "sales_impact_pct": sales_impact_pct,
            "projected_consolidated_net_income": projected_consolidated_net_income_2025,
            "projected_consolidated_sales": projected_consolidated_sales_2025
        }
        
        # Generate HTML
        print("\nStep 6: Generating HTML report...")
        html_content = generate_html_report(
            apps=apps,
            top_10_performers=top_10_performers,
            bottom_10_performers=bottom_10_performers,
            worst_entity=worst_entity,
            worst_entity_financials=worst_entity_financials,
            consolidated_net_income=consolidated_net_income,
            consolidated_sales=consolidated_sales,
            projected_impact=projected_impact
        )
        
        # Save HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Comprehensive_Entity_Analysis_2024_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[OK] HTML report saved to: {filename}")
        print(f"\nOpen the file in your browser to view the report!")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        await close_agent()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

