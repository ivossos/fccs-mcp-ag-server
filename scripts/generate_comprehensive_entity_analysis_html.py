"""Generate comprehensive HTML report for entity analysis including divestment simulation."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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


async def get_monthly_performance(entity_name: str, year: str = "FY25") -> dict[str, float]:
    """Get monthly Net Income for an entity."""
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


def load_entity_aliases() -> dict[str, str]:
    """Load entity aliases from CSV file."""
    alias_map = {}
    csv_file = Path("Ravi_ExportedMetadata_Entity.csv")
    if csv_file.exists():
        try:
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
            for encoding in encodings:
                try:
                    with open(csv_file, "r", encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            entity_name = row.get("Entity", "").strip()
                            alias = row.get("Alias: Default", "").strip()
                            if entity_name and alias:
                                alias_map[entity_name] = alias
                    break
                except Exception:
                    if encoding == encodings[-1]:
                        raise
                    continue
        except Exception:
            pass
    return alias_map


def format_entity_name(entity_code: str, alias_map: dict[str, str]) -> str:
    """Format entity name with alias if available."""
    alias = alias_map.get(entity_code)
    if alias and alias != entity_code:
        return f"{alias} ({entity_code})"
    return entity_code


def generate_html_report(
    app_name: str,
    total_2024: Optional[float],
    top_10_performers_2024: list[dict],
    top_10_underperformers_2024: list[dict],
    worst_entity: dict,
    worst_entity_year: str,
    monthly_data: dict[str, float],
    mid_year_loss: float,
    estimated_sale_price: float,
    current_consolidated: float,
    new_consolidated: float,
    improvement: float,
    pct_improvement: float,
    alias_map: dict[str, str]
) -> str:
    """Generate HTML report content."""
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M:%S")
    date_only = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    worst_entity_display = format_entity_name(worst_entity['entity'], alias_map)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Entity Analysis Report - {date_only}</title>
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
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
            font-size: 1.8em;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        .header-info {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .header-info p {{
            margin: 5px 0;
        }}
        .metric-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .metric-box h3 {{
            color: white;
            margin: 0 0 10px 0;
            border: none;
            padding: 0;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
        }}
        tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tbody tr:hover {{
            background-color: #e8f4f8;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .highlight-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .success-box {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .monthly-chart {{
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 300px;
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .month-bar {{
            flex: 1;
            margin: 0 5px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
        }}
        .bar {{
            width: 100%;
            background: linear-gradient(to top, #e74c3c, #c0392b);
            border-radius: 4px 4px 0 0;
            min-height: 10px;
            position: relative;
        }}
        .bar-value {{
            position: absolute;
            top: -25px;
            font-size: 11px;
            font-weight: bold;
            color: #333;
            white-space: nowrap;
        }}
        .month-label {{
            margin-top: 10px;
            font-size: 12px;
            font-weight: bold;
            color: #555;
        }}
        .impact-table {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .impact-table table {{
            box-shadow: none;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Comprehensive Entity Analysis Report</h1>
        
        <div class="header-info">
            <p><strong>Application:</strong> {app_name}</p>
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Report Type:</strong> Entity Performance Analysis & Divestment Simulation</p>
        </div>

        <h2>1. Application Information</h2>
        <div class="metric-box">
            <h3>FCCS Application</h3>
            <div class="metric-value">{app_name}</div>
            <p>Connection Status: Connected</p>
        </div>

        <h2>2. Executive Summary</h2>
        <div class="metric-box">
            <h3>Consolidated Net Income - FY24 YTD</h3>
            <div class="metric-value {'negative' if total_2024 and total_2024 < 0 else 'positive'}">
                ${f"{total_2024:,.2f}" if total_2024 else "N/A"}
            </div>
        </div>

        <h2>3. Top 10 Performing Entities - 2024 Actuals</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th style="text-align: right;">Net Income ($)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for i, perf in enumerate(top_10_performers_2024, 1):
        entity_display = format_entity_name(perf['entity'], alias_map)
        html += f"""
                <tr>
                    <td><strong>{i}</strong></td>
                    <td>{entity_display}</td>
                    <td style="text-align: right;" class="positive">${perf['net_income']:,.2f}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>

        <h2>4. Top 10 Underperforming Entities - 2024 Actuals</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th style="text-align: right;">Net Income ($)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for i, perf in enumerate(top_10_underperformers_2024, 1):
        entity_display = format_entity_name(perf['entity'], alias_map)
        html += f"""
                <tr>
                    <td><strong>{i}</strong></td>
                    <td>{entity_display}</td>
                    <td style="text-align: right;" class="negative">${perf['net_income']:,.2f}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>

        <h2>5. Divestment Simulation - Worst Performing Entity</h2>
        
        <div class="highlight-box">
            <h3>Entity Identified for Divestment</h3>
            <p><strong>Entity:</strong> {worst_entity_display}</p>
            <p><strong>Net Income ({worst_entity_year} YTD):</strong> <span class="negative">${worst_entity['net_income']:,.2f}</span></p>
            <p><strong>Divestment Date:</strong> Mid-Year 2025 (June)</p>
        </div>

        <h3>Monthly Performance Trend (YTD Values)</h3>
        <div class="monthly-chart">
"""
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    max_value = max([abs(v) for v in monthly_data.values()] + [1])
    
    for month in months:
        if month in monthly_data:
            value = monthly_data[month]
            height_pct = (abs(value) / max_value) * 100
            html += f"""
            <div class="month-bar">
                <div class="bar" style="height: {height_pct}%;">
                    <span class="bar-value">${value:,.0f}</span>
                </div>
                <div class="month-label">{month}</div>
            </div>
"""
    
    html += f"""
        </div>

        <h3>Divestment Details</h3>
        <div class="impact-table">
            <table>
                <tr>
                    <th>Metric</th>
                    <th style="text-align: right;">Amount</th>
                </tr>
                <tr>
                    <td>Mid-Year 2025 (June) YTD Loss</td>
                    <td style="text-align: right;" class="negative">${mid_year_loss:,.2f}</td>
                </tr>
                <tr>
                    <td>Estimated Sale Price</td>
                    <td style="text-align: right;" class="positive">${estimated_sale_price:,.2f}</td>
                </tr>
            </table>
        </div>

        <h2>6. Impact on Consolidated Group</h2>
        
        <div class="impact-table">
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Current Consolidated Net Income (FY25 YTD)</strong></td>
                        <td style="text-align: right;" class="{'negative' if current_consolidated < 0 else 'positive'}">
                            <strong>${current_consolidated:,.2f}</strong>
                        </td>
                    </tr>
                    <tr>
                        <td>Entity Loss Removed (June YTD)</td>
                        <td style="text-align: right;" class="negative">${mid_year_loss:,.2f}</td>
                    </tr>
                    <tr>
                        <td>Estimated Sale Proceeds</td>
                        <td style="text-align: right;" class="positive">${estimated_sale_price:,.2f}</td>
                    </tr>
                    <tr style="background: #e8f5e9; font-weight: bold;">
                        <td><strong>New Consolidated Net Income</strong></td>
                        <td style="text-align: right;" class="{'negative' if new_consolidated < 0 else 'positive'}">
                            <strong>${new_consolidated:,.2f}</strong>
                        </td>
                    </tr>
                    <tr style="background: #c8e6c9; font-weight: bold; font-size: 1.1em;">
                        <td><strong>Improvement</strong></td>
                        <td style="text-align: right;" class="positive">
                            <strong>${improvement:,.2f}</strong>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="metric-box">
            <h3>Percentage Improvement</h3>
            <div class="metric-value positive">{pct_improvement:.1f}%</div>
        </div>

        <h2>7. Recommendation</h2>
"""
    
    if improvement > 0:
        html += f"""
        <div class="success-box">
            <h3>✅ Proceed with Divestment</h3>
            <p>The divestment of <strong>{worst_entity_display}</strong> would significantly improve consolidated results.</p>
            <ul style="margin-top: 15px; margin-left: 20px;">
                <li><strong>Expected Improvement:</strong> ${improvement:,.2f}</li>
                <li><strong>Percentage Improvement:</strong> {pct_improvement:.1f}%</li>
                <li><strong>Divestment Date:</strong> Mid-Year 2025 (June)</li>
                <li><strong>Estimated Sale Price:</strong> ${estimated_sale_price:,.2f}</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Impact:</strong> The divestment would transform the consolidated group from a 
            <span class="negative">${current_consolidated:,.2f}</span> loss to a 
            <span class="positive">${new_consolidated:,.2f}</span> profit.</p>
        </div>
"""
    else:
        html += f"""
        <div class="warning-box">
            <h3>⚠️ Review Divestment Terms</h3>
            <p>Current divestment terms show a negative impact. Consider renegotiating sale price or timing.</p>
            <ul style="margin-top: 15px; margin-left: 20px;">
                <li><strong>Expected Impact:</strong> ${improvement:,.2f}</li>
                <li><strong>Recommendation:</strong> Review sale price or divestment timing</li>
            </ul>
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p>Generated by FCCS Comprehensive Entity Analysis Tool</p>
            <p>{timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def generate_comprehensive_html_report():
    """Generate comprehensive HTML report."""
    print("=" * 80)
    print("GENERATING COMPREHENSIVE ENTITY ANALYSIS HTML REPORT")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Load entity aliases
        print("Loading entity aliases...")
        alias_map = load_entity_aliases()
        print(f"[OK] Loaded {len(alias_map)} entity aliases")
        print()
        
        # Step 1: Get app info
        print("Getting application information...")
        app_info = await get_application_info()
        app_name = "Consol"
        if app_info.get("status") == "success":
            apps_data = app_info.get("data", {})
            apps = apps_data.get("items", [])
            if apps:
                app_name = apps[0].get("name", "Consol")
        print(f"[OK] Application: {app_name}")
        print()
        
        # Step 2: Get total for 2024
        print("Getting consolidated total for FY24...")
        total_2024 = await query_entity_performance("FCCS_Total Geography", "FY24")
        print(f"[OK] Total Net Income (FY24 YTD): ${total_2024:,.2f}" if total_2024 else "[OK] No data")
        print()
        
        # Step 3: Get entities and performance data
        print("Loading entities from cache...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        if not cached_entities or not cached_entities.get("items"):
            print("[ERROR] No entities found in cache")
            await close_agent()
            return
        
        entities_to_query = [item.get("name") for item in cached_entities["items"] if item.get("name")]
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total", "Consolidated", "Segment"]
        individual_entities = [
            e for e in entities_to_query 
            if not any(keyword in e for keyword in exclude_keywords)
        ]
        
        print(f"[OK] Found {len(individual_entities)} individual entities")
        print()
        
        # Get 2024 performance
        print(f"Querying Net Income for {len(individual_entities)} entities (FY24)...")
        print("(This may take a while)")
        print()
        
        entity_performance_2024 = []
        queried = 0
        
        for entity in individual_entities:
            queried += 1
            if queried % 10 == 0:
                print(f"  Progress: {queried}/{len(individual_entities)}...")
            
            value = await query_entity_performance(entity, "FY24")
            if value is not None:
                entity_performance_2024.append({
                    "entity": entity,
                    "net_income": value
                })
        
        print()
        print(f"[OK] Retrieved data for {len(entity_performance_2024)} entities")
        print()
        
        # Get top 10 performers and underperformers
        entity_performance_2024.sort(key=lambda x: x["net_income"], reverse=True)
        top_10_performers_2024 = entity_performance_2024[:10]
        
        entity_performance_2024.sort(key=lambda x: x["net_income"])
        top_10_underperformers_2024 = entity_performance_2024[:10]
        worst_entity_2024 = top_10_underperformers_2024[0] if top_10_underperformers_2024 else None
        
        # Get 2025 performance for divestment simulation
        print("Querying FY25 performance for divestment simulation...")
        entity_performance_2025 = []
        queried = 0
        
        for entity in individual_entities:
            queried += 1
            if queried % 10 == 0:
                print(f"  Progress: {queried}/{len(individual_entities)}...")
            
            value = await query_entity_performance(entity, "FY25")
            if value is not None:
                entity_performance_2025.append({
                    "entity": entity,
                    "net_income": value
                })
        
        print()
        
        if not entity_performance_2025:
            print("[WARNING] No FY25 data, using 2024 worst performer")
            worst_entity = worst_entity_2024
            worst_entity_year = "FY24"
        else:
            entity_performance_2025.sort(key=lambda x: x["net_income"])
            worst_entity = entity_performance_2025[0]
            worst_entity_year = "FY25"
        
        print(f"[OK] Worst performer identified: {format_entity_name(worst_entity['entity'], alias_map)}")
        print()
        
        # Get monthly performance
        print("Getting monthly performance data...")
        monthly_data = await get_monthly_performance(worst_entity['entity'], "FY25")
        if not monthly_data:
            monthly_data = {"Jun": worst_entity['net_income']}
        
        mid_year_month = "Jun"
        mid_year_loss = monthly_data.get(mid_year_month, worst_entity['net_income'])
        estimated_sale_price = abs(worst_entity['net_income']) * 0.5
        
        print("[OK] Monthly data collected")
        print()
        
        # Get consolidated results
        print("Getting consolidated results...")
        consolidated_result = await query_entity_performance("FCCS_Total Geography", "FY25")
        if consolidated_result is None:
            consolidated_result = await query_entity_performance("FCCS_Total Geography", "FY24")
        
        if consolidated_result is None:
            print("[ERROR] Could not get consolidated results")
            await close_agent()
            return
        
        current_consolidated = consolidated_result
        new_consolidated = current_consolidated - mid_year_loss + estimated_sale_price
        improvement = new_consolidated - current_consolidated
        pct_improvement = (improvement / abs(current_consolidated)) * 100 if current_consolidated != 0 else 0
        
        print("[OK] Impact calculated")
        print()
        
        # Generate HTML
        print("Generating HTML report...")
        html_content = generate_html_report(
            app_name=app_name,
            total_2024=total_2024,
            top_10_performers_2024=top_10_performers_2024,
            top_10_underperformers_2024=top_10_underperformers_2024,
            worst_entity=worst_entity,
            worst_entity_year=worst_entity_year,
            monthly_data=monthly_data,
            mid_year_loss=mid_year_loss,
            estimated_sale_price=estimated_sale_price,
            current_consolidated=current_consolidated,
            new_consolidated=new_consolidated,
            improvement=improvement,
            pct_improvement=pct_improvement,
            alias_map=alias_map
        )
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Comprehensive_Entity_Analysis_Report_{timestamp}.html"
        report_path = Path(report_filename)
        report_path.write_text(html_content, encoding="utf-8")
        
        print("=" * 80)
        print("HTML REPORT GENERATED")
        print("=" * 80)
        print(f"File: {report_filename}")
        print(f"Path: {report_path.absolute()}")
        print()
        print("Report includes:")
        print("  - Application information")
        print("  - Top 10 performing entities (2024)")
        print("  - Top 10 underperforming entities (2024)")
        print("  - Divestment simulation for worst performer")
        print("  - Impact analysis on consolidated group")
        print("  - Recommendations")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_comprehensive_html_report())



