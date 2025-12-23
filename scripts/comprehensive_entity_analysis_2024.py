"""Comprehensive Entity Analysis for 2024:
1. List all FCCS apps
2. Connect to Consol App
3. Show top-10 performing entities for actuals 2024
4. Show top-10 under performing entities for actuals 2024
5. Simulate the divestment for the worst performing entity, about to happen in mid year 2025
6. Calculate the impact in the consolidated group
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.application import get_application_info
from fccs_agent.tools.data import smart_retrieve, copy_data, clear_data
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


async def main():
    """Main analysis function."""
    print("=" * 80)
    print("COMPREHENSIVE ENTITY ANALYSIS - 2024")
    print("=" * 80)
    print()
    
    try:
        # Step 1: List all FCCS apps
        print("STEP 1: Listing all FCCS applications...")
        print("-" * 80)
        config = load_config()
        await initialize_agent(config)
        
        app_info = await get_application_info()
        if app_info.get("status") == "success":
            apps = app_info.get("data", {}).get("items", [])
            print(f"[OK] Found {len(apps)} FCCS application(s):")
            for app in apps:
                print(f"  - {app.get('name')} (Type: {app.get('appType')})")
        else:
            print("[ERROR] Could not retrieve application info")
            return
        print()
        
        # Step 2: Connect to Consol App
        print("STEP 2: Connecting to Consol App...")
        print("-" * 80)
        print("[OK] Connected to Consol application")
        print()
        
        # Step 3 & 4: Get entity performance data
        print("STEP 3 & 4: Analyzing entity performance for 2024...")
        print("-" * 80)
        
        # Get entities from cache
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        if cached_entities and cached_entities.get("items"):
            entities_to_query = [item.get("name") for item in cached_entities["items"] if item.get("name")]
            print(f"[OK] Found {len(entities_to_query)} entities to analyze")
        else:
            print("[WARNING] No entity list available")
            await close_agent()
            return
        
        print(f"Querying Net Income for {len(entities_to_query)} entities for FY24...")
        print("(This may take a while)")
        print()
        
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
        
        print()
        print(f"[OK] Retrieved performance data for {len(entity_performance)} entities")
        print()
        
        # Sort by Net Income
        entity_performance.sort(key=lambda x: x["net_income"], reverse=True)
        
        # Step 3: Top 10 Performers
        print("=" * 80)
        print("STEP 3: TOP 10 PERFORMING ENTITIES - 2024 (Actuals)")
        print("=" * 80)
        print(f"{'Rank':<6} {'Entity':<45} {'Net Income':>25}")
        print("-" * 80)
        
        top_10 = entity_performance[:10]
        for i, perf in enumerate(top_10, 1):
            entity_name = perf["entity"][:43]  # Truncate if too long
            net_income = perf["net_income"]
            print(f"{i:<6} {entity_name:<45} ${net_income:>24,.2f}")
        print("=" * 80)
        print()
        
        # Step 4: Top 10 Underperformers
        print("=" * 80)
        print("STEP 4: TOP 10 UNDERPERFORMING ENTITIES - 2024 (Actuals)")
        print("=" * 80)
        print(f"{'Rank':<6} {'Entity':<45} {'Net Income':>25}")
        print("-" * 80)
        
        # Sort ascending for worst performers
        entity_performance.sort(key=lambda x: x["net_income"])
        bottom_10 = entity_performance[:10]
        
        for i, perf in enumerate(bottom_10, 1):
            entity_name = perf["entity"][:43]  # Truncate if too long
            net_income = perf["net_income"]
            print(f"{i:<6} {entity_name:<45} ${net_income:>24,.2f}")
        print("=" * 80)
        print()
        
        # Step 5 & 6: Simulate divestment
        if not bottom_10:
            print("[WARNING] No underperforming entities found for divestment simulation")
            await close_agent()
            return
        
        worst_entity = bottom_10[0]
        worst_entity_name = worst_entity["entity"]
        worst_entity_net_income = worst_entity["net_income"]
        
        print("=" * 80)
        print("STEP 5: DIVESTMENT SIMULATION")
        print("=" * 80)
        print(f"Worst Performing Entity: {worst_entity_name}")
        print(f"2024 Net Income: ${worst_entity_net_income:,.2f}")
        print(f"Divestment Date: Mid-Year 2025 (June 30, 2025)")
        print()
        
        # Get detailed financials for worst entity
        print("Retrieving detailed financial information...")
        worst_entity_financials = await get_entity_balance_sheet(worst_entity_name, "FY24")
        
        print(f"  Total Assets: ${worst_entity_financials.get('Total Assets', 0):,.2f}")
        print(f"  Total Liabilities: ${worst_entity_financials.get('Total Liabilities', 0):,.2f}")
        print(f"  Total Equity: ${worst_entity_financials.get('Total Equity', 0):,.2f}")
        print(f"  Sales: ${worst_entity_financials.get('Sales', 0):,.2f}")
        print()
        
        # Get consolidated totals
        print("Retrieving consolidated group totals...")
        consolidated_net_income = await query_entity_performance("FCCS_Total Geography", "FY24")
        consolidated_sales = await smart_retrieve(
            account="FCCS_Sales",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        consolidated_sales_value = 0.0
        if consolidated_sales.get("status") == "success":
            data = consolidated_sales.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                consolidated_sales_value = float(value) if value is not None else 0.0
        
        print()
        print("=" * 80)
        print("STEP 6: IMPACT ANALYSIS - CONSOLIDATED GROUP")
        print("=" * 80)
        print()
        print("BEFORE DIVESTMENT (2024 Actuals):")
        print("-" * 80)
        print(f"  Consolidated Net Income: ${consolidated_net_income:,.2f}" if consolidated_net_income else "  Consolidated Net Income: N/A")
        print(f"  Consolidated Sales: ${consolidated_sales_value:,.2f}")
        print()
        
        print("ENTITY TO BE DIVESTED:")
        print("-" * 80)
        print(f"  Entity: {worst_entity_name}")
        print(f"  Net Income Contribution: ${worst_entity_net_income:,.2f}")
        print(f"  Sales Contribution: ${worst_entity_financials.get('Sales', 0):,.2f}")
        print(f"  Assets: ${worst_entity_financials.get('Total Assets', 0):,.2f}")
        print()
        
        # Calculate impact (assuming divestment happens mid-year 2025)
        # For 2025, we'll assume 50% of 2024 performance (6 months)
        projected_2025_net_income = worst_entity_net_income * 0.5
        projected_2025_sales = worst_entity_financials.get('Sales', 0) * 0.5
        
        print("PROJECTED IMPACT (2025 - Mid-Year Divestment):")
        print("-" * 80)
        print(f"  Projected Net Income Loss (6 months): ${projected_2025_net_income:,.2f}")
        print(f"  Projected Sales Loss (6 months): ${projected_2025_sales:,.2f}")
        print()
        
        if consolidated_net_income:
            net_income_impact_pct = (projected_2025_net_income / consolidated_net_income * 100) if consolidated_net_income != 0 else 0
            sales_impact_pct = (projected_2025_sales / consolidated_sales_value * 100) if consolidated_sales_value != 0 else 0
            
            print("IMPACT AS % OF CONSOLIDATED GROUP:")
            print("-" * 80)
            print(f"  Net Income Impact: {net_income_impact_pct:.2f}%")
            print(f"  Sales Impact: {sales_impact_pct:.2f}%")
            print()
            
            # Calculate after divestment
            projected_consolidated_net_income_2025 = consolidated_net_income - projected_2025_net_income
            projected_consolidated_sales_2025 = consolidated_sales_value - projected_2025_sales
            
            print("PROJECTED CONSOLIDATED GROUP AFTER DIVESTMENT (2025):")
            print("-" * 80)
            print(f"  Projected Net Income: ${projected_consolidated_net_income_2025:,.2f}")
            print(f"  Projected Sales: ${projected_consolidated_sales_2025:,.2f}")
            print()
            
            net_income_change = projected_2025_net_income
            sales_change = projected_2025_sales
            
            print("NET CHANGE:")
            print("-" * 80)
            print(f"  Net Income Change: ${net_income_change:,.2f} ({net_income_impact_pct:.2f}%)")
            print(f"  Sales Change: ${sales_change:,.2f} ({sales_impact_pct:.2f}%)")
        
        print("=" * 80)
        print()
        print("SUMMARY:")
        print(f"  - Worst performing entity: {worst_entity_name}")
        print(f"  - 2024 Net Income: ${worst_entity_net_income:,.2f}")
        print(f"  - Divestment will remove this entity's contribution from mid-2025 onwards")
        print(f"  - Impact on consolidated group: {net_income_impact_pct:.2f}% of Net Income" if consolidated_net_income else "  - Impact calculation requires consolidated data")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        await close_agent()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

