"""Comprehensive Financial Analysis for FY25 YTD using MCP tools - HTML Report.

This script generates:
1. Top 10 entities by revenue
2. Bottom 5 entities by profit margin
3. Largest variances vs FY24
4. Intercompany matching status
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import MCP client directly
from fccs_agent.client.fccs_client import FccsClient
from fccs_agent.config import load_config
from fccs_agent.utils.cache import load_members_from_cache


async def get_account_value_mcp(
    client: FccsClient,
    app_name: str,
    account: str,
    entity: str,
    year: str,
    period: str = "Dec"
) -> Optional[float]:
    """Get account value for an entity using MCP client."""
    try:
        grid_definition = {
            "suppressMissingBlocks": True,
            "pov": {
                "members": [
                    [year], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                    ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                    ["FCCS_Mvmts_Total"], [entity], ["Entity Currency"],
                    ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                    ["Total Custom 4"]
                ]
            },
            "columns": [{"members": [[period]]}],
            "rows": [{"members": [[account]]}]
        }
        
        result = await client.export_data_slice(app_name, "Consol", grid_definition)
        
        if result and "rows" in result:
            rows = result.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else None
    except Exception:
        pass
    return None


async def get_entity_metrics_mcp(
    client: FccsClient,
    app_name: str,
    entity: str
) -> Dict:
    """Get revenue, net income, and profit margin for FY24 and FY25."""
    metrics = {
        "entity": entity,
        "fy24": {"revenue": None, "net_income": None, "profit_margin": None},
        "fy25": {"revenue": None, "net_income": None, "profit_margin": None},
        "variance": {"revenue": None, "net_income": None, "revenue_pct": None, "net_income_pct": None}
    }
    
    # Get FY24 data
    fy24_revenue = await get_account_value_mcp(client, app_name, "FCCS_Sales", entity, "FY24", "Dec")
    fy24_net_income = await get_account_value_mcp(client, app_name, "FCCS_Net Income", entity, "FY24", "Dec")
    
    metrics["fy24"]["revenue"] = fy24_revenue
    metrics["fy24"]["net_income"] = fy24_net_income
    if fy24_revenue and fy24_revenue != 0:
        metrics["fy24"]["profit_margin"] = (fy24_net_income / fy24_revenue * 100) if fy24_net_income else None
    
    # Get FY25 data
    fy25_revenue = await get_account_value_mcp(client, app_name, "FCCS_Sales", entity, "FY25", "Dec")
    fy25_net_income = await get_account_value_mcp(client, app_name, "FCCS_Net Income", entity, "FY25", "Dec")
    
    metrics["fy25"]["revenue"] = fy25_revenue
    metrics["fy25"]["net_income"] = fy25_net_income
    if fy25_revenue and fy25_revenue != 0:
        metrics["fy25"]["profit_margin"] = (fy25_net_income / fy25_revenue * 100) if fy25_net_income else None
    
    # Calculate variances
    if fy24_revenue is not None and fy25_revenue is not None:
        metrics["variance"]["revenue"] = fy25_revenue - fy24_revenue
        if fy24_revenue != 0:
            metrics["variance"]["revenue_pct"] = (metrics["variance"]["revenue"] / abs(fy24_revenue)) * 100
    
    if fy24_net_income is not None and fy25_net_income is not None:
        metrics["variance"]["net_income"] = fy25_net_income - fy24_net_income
        if fy24_net_income != 0:
            metrics["variance"]["net_income_pct"] = (metrics["variance"]["net_income"] / abs(fy24_net_income)) * 100
    
    return metrics


def generate_html_report(
    top_revenue: List[Dict],
    bottom_margin: List[Dict],
    revenue_variances: List[Dict],
    net_income_variances: List[Dict],
    ic_status: Dict,
    summary_stats: Dict
) -> str:
    """Generate comprehensive HTML report."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Financial Analysis - FY25 YTD</title>
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
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f8ff;
        }}
        .positive {{
            color: #27ae60;
            font-weight: 600;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: 600;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #bdc3c7;
        }}
        .summary-item:last-child {{
            border-bottom: none;
        }}
        .summary-label {{
            font-weight: 600;
            color: #2c3e50;
        }}
        .summary-value {{
            color: #34495e;
        }}
        .ic-status {{
            padding: 15px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .rank {{
            font-weight: bold;
            color: #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Comprehensive Financial Analysis - FY25 YTD</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-box">
            <h3>Executive Summary</h3>
            <div class="summary-item">
                <span class="summary-label">Total Entities Analyzed:</span>
                <span class="summary-value">{summary_stats['total_entities']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Total FY25 YTD Revenue:</span>
                <span class="summary-value">${summary_stats['total_fy25_revenue']:,.2f}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Total FY25 YTD Net Income:</span>
                <span class="summary-value">${summary_stats['total_fy25_net_income']:,.2f}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Overall Profit Margin:</span>
                <span class="summary-value">{summary_stats['overall_margin']:.2f}%</span>
            </div>
            {f'''
            <div class="summary-item">
                <span class="summary-label">Revenue Variance vs FY24:</span>
                <span class="summary-value {'positive' if summary_stats.get('revenue_variance', 0) >= 0 else 'negative'}">
                    ${summary_stats.get('revenue_variance', 0):,.2f} ({summary_stats.get('revenue_variance_pct', 0):+.2f}%)
                </span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Net Income Variance vs FY24:</span>
                <span class="summary-value {'positive' if summary_stats.get('net_income_variance', 0) >= 0 else 'negative'}">
                    ${summary_stats.get('net_income_variance', 0):,.2f} ({summary_stats.get('net_income_variance_pct', 0):+.2f}%)
                </span>
            </div>
            ''' if summary_stats.get('revenue_variance') is not None else ''}
        </div>
        
        <h2>1. Top 10 Entities by Revenue (FY25 YTD)</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th>Revenue (FY25)</th>
                    <th>Net Income</th>
                    <th>Profit Margin</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for rank, metrics in enumerate(top_revenue, 1):
        revenue = metrics["fy25"]["revenue"] or 0
        net_income = metrics["fy25"]["net_income"] or 0
        margin = metrics["fy25"]["profit_margin"] or 0
        margin_class = "positive" if margin >= 0 else "negative"
        
        html += f"""
                <tr>
                    <td class="rank">{rank}</td>
                    <td>{metrics["entity"]}</td>
                    <td>${revenue:,.2f}</td>
                    <td class="{'positive' if net_income >= 0 else 'negative'}">${net_income:,.2f}</td>
                    <td class="{margin_class}">{margin:.2f}%</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h2>2. Bottom 5 Entities by Profit Margin (FY25 YTD)</h2>
        <p><em>Entities with revenue > 0 and lowest profit margins</em></p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th>Revenue</th>
                    <th>Net Income</th>
                    <th>Profit Margin</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for rank, metrics in enumerate(bottom_margin, 1):
        revenue = metrics["fy25"]["revenue"] or 0
        net_income = metrics["fy25"]["net_income"] or 0
        margin = metrics["fy25"]["profit_margin"] or 0
        margin_class = "positive" if margin >= 0 else "negative"
        
        html += f"""
                <tr>
                    <td class="rank">{rank}</td>
                    <td>{metrics["entity"]}</td>
                    <td>${revenue:,.2f}</td>
                    <td class="{'positive' if net_income >= 0 else 'negative'}">${net_income:,.2f}</td>
                    <td class="{margin_class}">{margin:.2f}%</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h2>3. Largest Variances vs FY24</h2>
        
        <h3>3a. Top 10 Largest Revenue Variances (Absolute)</h3>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th>FY24 Revenue</th>
                    <th>FY25 Revenue</th>
                    <th>Variance</th>
                    <th>% Change</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for rank, metrics in enumerate(revenue_variances, 1):
        fy24_rev = metrics["fy24"]["revenue"] or 0
        fy25_rev = metrics["fy25"]["revenue"] or 0
        variance = metrics["variance"]["revenue"] or 0
        pct_change = metrics["variance"]["revenue_pct"] or 0
        variance_class = "positive" if variance >= 0 else "negative"
        
        html += f"""
                <tr>
                    <td class="rank">{rank}</td>
                    <td>{metrics["entity"]}</td>
                    <td>${fy24_rev:,.2f}</td>
                    <td>${fy25_rev:,.2f}</td>
                    <td class="{variance_class}">${variance:,.2f}</td>
                    <td class="{variance_class}">{pct_change:+.2f}%</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h3>3b. Top 10 Largest Net Income Variances (Absolute)</h3>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th>FY24 Net Income</th>
                    <th>FY25 Net Income</th>
                    <th>Variance</th>
                    <th>% Change</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for rank, metrics in enumerate(net_income_variances, 1):
        fy24_ni = metrics["fy24"]["net_income"] or 0
        fy25_ni = metrics["fy25"]["net_income"] or 0
        variance = metrics["variance"]["net_income"] or 0
        pct_change = metrics["variance"]["net_income_pct"] or 0
        variance_class = "positive" if variance >= 0 else "negative"
        
        html += f"""
                <tr>
                    <td class="rank">{rank}</td>
                    <td>{metrics["entity"]}</td>
                    <td class="{'positive' if fy24_ni >= 0 else 'negative'}">${fy24_ni:,.2f}</td>
                    <td class="{'positive' if fy25_ni >= 0 else 'negative'}">${fy25_ni:,.2f}</td>
                    <td class="{variance_class}">${variance:,.2f}</td>
                    <td class="{variance_class}">{pct_change:+.2f}%</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <h2>4. Intercompany Matching Status</h2>
"""
    
    if ic_status.get("status") == "success":
        html += f"""
        <div class="ic-status">
            <strong>✅ Status:</strong> Intercompany matching report generated successfully<br>
            <strong>Details:</strong> {ic_status.get('message', 'Report available')}
        </div>
"""
    else:
        html += f"""
        <div class="ic-status">
            <strong>⚠️ Status:</strong> Could not generate intercompany matching report automatically<br>
            <strong>Reason:</strong> {ic_status.get('error', 'Report may require manual execution or additional permissions')}<br>
            <strong>Recommendation:</strong> Please run the intercompany matching report manually in FCCS for FY25 YTD (Dec period).
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p>Comprehensive Financial Analysis Report | Generated by FCCS MCP Agent</p>
            <p>Report Timestamp: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def generate_comprehensive_analysis():
    """Generate comprehensive financial analysis for FY25 YTD."""
    print("=" * 100)
    print("COMPREHENSIVE FINANCIAL ANALYSIS - FY25 YTD")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        config = load_config()
        client = FccsClient(config)
        app_name = "Consol"
        
        print("[OK] Connected to FCCS")
        print()
        
        # Load entity list from cache
        print("Loading entity list...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        entities = [item.get("name") for item in cached_entities.get("items", []) if item.get("name")]
        
        # Filter out totals and system entities
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total", "FCCS_Global Assumptions", 
                          "Elim", "Segment", "Consolidated", "Consolidation"]
        individual_entities = [
            e for e in entities 
            if not any(kw in e for kw in exclude_keywords) and e not in ["Root"]
        ]
        
        print(f"[OK] Found {len(individual_entities)} individual entities")
        print()
        
        # Collect metrics for all entities
        print("Collecting financial metrics for all entities...")
        print("(This may take several minutes...)")
        print()
        
        all_metrics = []
        processed = 0
        
        for entity in individual_entities:
            if processed % 50 == 0:
                print(f"  Processed {processed}/{len(individual_entities)} entities...")
            
            metrics = await get_entity_metrics_mcp(client, app_name, entity)
            
            # Only include entities with FY25 revenue data
            if metrics["fy25"]["revenue"] is not None:
                all_metrics.append(metrics)
            
            processed += 1
        
        print(f"[OK] Collected metrics for {len(all_metrics)} entities with FY25 data")
        print()
        
        # 1. TOP 10 ENTITIES BY REVENUE
        top_revenue = sorted(
            all_metrics,
            key=lambda x: x["fy25"]["revenue"] if x["fy25"]["revenue"] else float('-inf'),
            reverse=True
        )[:10]
        
        print("[OK] Identified top 10 entities by revenue")
        
        # 2. BOTTOM 5 ENTITIES BY PROFIT MARGIN
        entities_with_revenue = [
            m for m in all_metrics 
            if m["fy25"]["revenue"] and m["fy25"]["revenue"] > 0
        ]
        
        bottom_margin = sorted(
            entities_with_revenue,
            key=lambda x: x["fy25"]["profit_margin"] if x["fy25"]["profit_margin"] is not None else float('inf')
        )[:5]
        
        print("[OK] Identified bottom 5 entities by profit margin")
        
        # 3. LARGEST VARIANCES VS FY24
        entities_with_variance = [
            m for m in all_metrics 
            if m["fy24"]["revenue"] is not None and m["fy25"]["revenue"] is not None
        ]
        
        revenue_variances = sorted(
            entities_with_variance,
            key=lambda x: abs(x["variance"]["revenue"]) if x["variance"]["revenue"] is not None else 0,
            reverse=True
        )[:10]
        
        net_income_variances = sorted(
            entities_with_variance,
            key=lambda x: abs(x["variance"]["net_income"]) if x["variance"]["net_income"] is not None else 0,
            reverse=True
        )[:10]
        
        print("[OK] Calculated largest variances vs FY24")
        
        # 4. INTERCOMPANY MATCHING STATUS
        print("Attempting to generate intercompany matching report...")
        ic_status = {"status": "error", "error": "Not available"}
        try:
            ic_result = await client.generate_intercompany_matching_report(
                app_name,
                {"scenario": "Actual", "year": "FY25", "period": "Dec"}
            )
            ic_status = {"status": "success", "message": "Report generated successfully"}
            print("[OK] Intercompany matching report generated successfully")
        except Exception as e:
            ic_status = {"status": "error", "error": str(e)}
            print(f"[WARNING] Could not generate intercompany matching report: {str(e)}")
        
        # SUMMARY STATISTICS
        total_fy25_revenue = sum(m["fy25"]["revenue"] or 0 for m in all_metrics)
        total_fy25_net_income = sum(m["fy25"]["net_income"] or 0 for m in all_metrics)
        total_fy24_revenue = sum(m["fy24"]["revenue"] or 0 for m in entities_with_variance)
        total_fy24_net_income = sum(m["fy24"]["net_income"] or 0 for m in entities_with_variance)
        
        overall_margin = (total_fy25_net_income / total_fy25_revenue * 100) if total_fy25_revenue > 0 else 0
        
        summary_stats = {
            "total_entities": len(all_metrics),
            "total_fy25_revenue": total_fy25_revenue,
            "total_fy25_net_income": total_fy25_net_income,
            "overall_margin": overall_margin
        }
        
        if total_fy24_revenue > 0:
            revenue_variance_total = total_fy25_revenue - total_fy24_revenue
            revenue_variance_pct = (revenue_variance_total / total_fy24_revenue) * 100
            summary_stats["revenue_variance"] = revenue_variance_total
            summary_stats["revenue_variance_pct"] = revenue_variance_pct
        
        if total_fy24_net_income != 0:
            net_income_variance_total = total_fy25_net_income - total_fy24_net_income
            net_income_variance_pct = (net_income_variance_total / abs(total_fy24_net_income)) * 100
            summary_stats["net_income_variance"] = net_income_variance_total
            summary_stats["net_income_variance_pct"] = net_income_variance_pct
        
        print("[OK] Calculated summary statistics")
        print()
        
        # Generate HTML report
        print("Generating HTML report...")
        html_content = generate_html_report(
            top_revenue,
            bottom_margin,
            revenue_variances,
            net_income_variances,
            ic_status,
            summary_stats
        )
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Comprehensive_FY25_Analysis_{timestamp}.html"
        report_path = Path(__file__).parent.parent / report_filename
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"[OK] Report saved to: {report_path}")
        print()
        print("=" * 100)
        print("ANALYSIS COMPLETE")
        print("=" * 100)
        print(f"Report file: {report_filename}")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(generate_comprehensive_analysis())

