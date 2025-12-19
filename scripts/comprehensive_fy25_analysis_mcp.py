"""Comprehensive Financial Analysis for FY25 YTD using MCP tools.

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
from fccs_agent.cache.members_cache import load_members_from_cache


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
        print("=" * 100)
        print("1. TOP 10 ENTITIES BY REVENUE (FY25 YTD)")
        print("=" * 100)
        print()
        
        top_revenue = sorted(
            all_metrics,
            key=lambda x: x["fy25"]["revenue"] if x["fy25"]["revenue"] else float('-inf'),
            reverse=True
        )[:10]
        
        print(f"{'Rank':<6} {'Entity':<40} {'Revenue (FY25)':>20} {'Net Income':>20} {'Margin %':>12}")
        print("-" * 100)
        
        for rank, metrics in enumerate(top_revenue, 1):
            entity = metrics["entity"][:38]  # Truncate if too long
            revenue = metrics["fy25"]["revenue"] or 0
            net_income = metrics["fy25"]["net_income"] or 0
            margin = metrics["fy25"]["profit_margin"] or 0
            
            print(f"{rank:<6} {entity:<40} ${revenue:>19,.2f} ${net_income:>19,.2f} {margin:>11.2f}%")
        
        print()
        
        # 2. BOTTOM 5 ENTITIES BY PROFIT MARGIN
        print("=" * 100)
        print("2. BOTTOM 5 ENTITIES BY PROFIT MARGIN (FY25 YTD)")
        print("=" * 100)
        print()
        print("(Entities with revenue > 0 and lowest profit margins)")
        print()
        
        # Filter entities with revenue > 0
        entities_with_revenue = [
            m for m in all_metrics 
            if m["fy25"]["revenue"] and m["fy25"]["revenue"] > 0
        ]
        
        bottom_margin = sorted(
            entities_with_revenue,
            key=lambda x: x["fy25"]["profit_margin"] if x["fy25"]["profit_margin"] is not None else float('inf')
        )[:5]
        
        print(f"{'Rank':<6} {'Entity':<40} {'Revenue':>20} {'Net Income':>20} {'Margin %':>12}")
        print("-" * 100)
        
        for rank, metrics in enumerate(bottom_margin, 1):
            entity = metrics["entity"][:38]
            revenue = metrics["fy25"]["revenue"] or 0
            net_income = metrics["fy25"]["net_income"] or 0
            margin = metrics["fy25"]["profit_margin"] or 0
            
            print(f"{rank:<6} {entity:<40} ${revenue:>19,.2f} ${net_income:>19,.2f} {margin:>11.2f}%")
        
        print()
        
        # 3. LARGEST VARIANCES VS FY24
        print("=" * 100)
        print("3. LARGEST VARIANCES VS FY24")
        print("=" * 100)
        print()
        
        # Filter entities with both FY24 and FY25 data
        entities_with_variance = [
            m for m in all_metrics 
            if m["fy24"]["revenue"] is not None and m["fy25"]["revenue"] is not None
        ]
        
        # Largest revenue variances (absolute)
        print("3a. TOP 10 LARGEST REVENUE VARIANCES (Absolute)")
        print("-" * 100)
        print()
        
        revenue_variances = sorted(
            entities_with_variance,
            key=lambda x: abs(x["variance"]["revenue"]) if x["variance"]["revenue"] is not None else 0,
            reverse=True
        )[:10]
        
        print(f"{'Rank':<6} {'Entity':<40} {'FY24 Revenue':>20} {'FY25 Revenue':>20} {'Variance':>20} {'% Change':>12}")
        print("-" * 100)
        
        for rank, metrics in enumerate(revenue_variances, 1):
            entity = metrics["entity"][:38]
            fy24_rev = metrics["fy24"]["revenue"] or 0
            fy25_rev = metrics["fy25"]["revenue"] or 0
            variance = metrics["variance"]["revenue"] or 0
            pct_change = metrics["variance"]["revenue_pct"] or 0
            
            print(f"{rank:<6} {entity:<40} ${fy24_rev:>19,.2f} ${fy25_rev:>19,.2f} ${variance:>19,.2f} {pct_change:>11.2f}%")
        
        print()
        print("3b. TOP 10 LARGEST NET INCOME VARIANCES (Absolute)")
        print("-" * 100)
        print()
        
        net_income_variances = sorted(
            entities_with_variance,
            key=lambda x: abs(x["variance"]["net_income"]) if x["variance"]["net_income"] is not None else 0,
            reverse=True
        )[:10]
        
        print(f"{'Rank':<6} {'Entity':<40} {'FY24 Net Inc':>20} {'FY25 Net Inc':>20} {'Variance':>20} {'% Change':>12}")
        print("-" * 100)
        
        for rank, metrics in enumerate(net_income_variances, 1):
            entity = metrics["entity"][:38]
            fy24_ni = metrics["fy24"]["net_income"] or 0
            fy25_ni = metrics["fy25"]["net_income"] or 0
            variance = metrics["variance"]["net_income"] or 0
            pct_change = metrics["variance"]["net_income_pct"] or 0
            
            print(f"{rank:<6} {entity:<40} ${fy24_ni:>19,.2f} ${fy25_ni:>19,.2f} ${variance:>19,.2f} {pct_change:>11.2f}%")
        
        print()
        
        # 4. INTERCOMPANY MATCHING STATUS
        print("=" * 100)
        print("4. INTERCOMPANY MATCHING STATUS")
        print("=" * 100)
        print()
        
        print("Attempting to generate intercompany matching report...")
        try:
            ic_result = await client.generate_intercompany_matching_report(
                app_name,
                {"scenario": "Actual", "year": "FY25", "period": "Dec"}
            )
            print("[OK] Intercompany matching report generated successfully")
            print(f"Result: {ic_result}")
        except Exception as e:
            print(f"[WARNING] Could not generate intercompany matching report: {str(e)}")
            print("  This may require additional permissions or the report may need to be run manually.")
        
        print()
        
        # SUMMARY STATISTICS
        print("=" * 100)
        print("SUMMARY STATISTICS")
        print("=" * 100)
        print()
        
        total_fy25_revenue = sum(m["fy25"]["revenue"] or 0 for m in all_metrics)
        total_fy25_net_income = sum(m["fy25"]["net_income"] or 0 for m in all_metrics)
        total_fy24_revenue = sum(m["fy24"]["revenue"] or 0 for m in entities_with_variance)
        total_fy24_net_income = sum(m["fy24"]["net_income"] or 0 for m in entities_with_variance)
        
        print(f"Total Entities Analyzed: {len(all_metrics)}")
        print(f"Entities with FY24 Comparison Data: {len(entities_with_variance)}")
        print()
        print(f"Total FY25 YTD Revenue:     ${total_fy25_revenue:>20,.2f}")
        print(f"Total FY25 YTD Net Income:  ${total_fy25_net_income:>20,.2f}")
        if total_fy25_revenue > 0:
            overall_margin = (total_fy25_net_income / total_fy25_revenue) * 100
            print(f"Overall Profit Margin:      {overall_margin:>20.2f}%")
        print()
        
        if total_fy24_revenue > 0:
            revenue_variance_total = total_fy25_revenue - total_fy24_revenue
            revenue_variance_pct = (revenue_variance_total / total_fy24_revenue) * 100
            print(f"Total FY24 YTD Revenue:     ${total_fy24_revenue:>20,.2f}")
            print(f"Revenue Variance:           ${revenue_variance_total:>20,.2f} ({revenue_variance_pct:+.2f}%)")
            print()
        
        if total_fy24_net_income != 0:
            net_income_variance_total = total_fy25_net_income - total_fy24_net_income
            net_income_variance_pct = (net_income_variance_total / abs(total_fy24_net_income)) * 100
            print(f"Total FY24 YTD Net Income:  ${total_fy24_net_income:>20,.2f}")
            print(f"Net Income Variance:        ${net_income_variance_total:>20,.2f} ({net_income_variance_pct:+.2f}%)")
        
        print()
        print("=" * 100)
        print("ANALYSIS COMPLETE")
        print("=" * 100)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(generate_comprehensive_analysis())








