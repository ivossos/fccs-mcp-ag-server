"""Divestiture Simulation - Analyze worst performer, find best sale month, and simulate impact."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


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


async def get_ytd_performance(entity_name: str, year: str = "FY25") -> Optional[float]:
    """Get YTD Net Income for an entity."""
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


async def simulate_divestiture():
    """Simulate divestiture of worst performer."""
    print("=" * 80)
    print("DIVESTITURE SIMULATION - Worst Performer Analysis")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Step 1: Identify worst performer for 2025
        print("STEP 1: Identifying Worst Performer for 2025")
        print("-" * 80)
        
        cached_entities = load_members_from_cache("Consol", "Entity")
        if not cached_entities or not cached_entities.get("items"):
            print("[ERROR] No entities found in cache")
            await close_agent()
            return
        
        entities = [item.get("name") for item in cached_entities["items"] if item.get("name")]
        
        # Exclude total/consolidated entities
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total", "Consolidated", "Segment"]
        individual_entities = [
            e for e in entities 
            if not any(keyword in e for keyword in exclude_keywords)
        ]
        
        print(f"Checking {len(individual_entities)} individual entities (excluding totals)...")
        
        entity_performance = []
        for entity in individual_entities:
            value = await get_ytd_performance(entity, "FY25")
            if value is not None:
                entity_performance.append({"entity": entity, "net_income": value})
        
        if not entity_performance:
            print("[ERROR] No performance data found")
            await close_agent()
            return
        
        # Sort to find worst (lowest Net Income)
        entity_performance.sort(key=lambda x: x["net_income"])
        worst_entity = entity_performance[0]
        
        print(f"Worst Performer: {worst_entity['entity']}")
        print(f"Net Income (FY25 YTD): ${worst_entity['net_income']:,.2f}")
        print()
        
        # Step 2: Get monthly performance to find best sale month
        print("STEP 2: Analyzing Monthly Performance to Find Best Sale Month")
        print("-" * 80)
        print(f"Getting monthly data for {worst_entity['entity']}...")
        
        monthly_data = await get_monthly_performance(worst_entity['entity'], "FY25")
        
        if not monthly_data:
            print("[WARNING] No monthly data available, using YTD data")
            monthly_data = {"Dec": worst_entity['net_income']}
        
        print()
        print("Monthly Net Income Performance (YTD values):")
        print(f"{'Month':<10} {'YTD Net Income':>20} {'Monthly Change':>20}")
        print("-" * 50)
        
        previous_ytd = 0
        best_month = None
        best_ytd = float('-inf')  # Start with worst possible, find least negative
        
        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
            if month in monthly_data:
                ytd_value = monthly_data[month]
                monthly_change = ytd_value - previous_ytd
                print(f"{month:<10} ${ytd_value:>19,.2f} ${monthly_change:>19,.2f}")
                
                # Best month to sell: when YTD loss is smallest (least negative)
                # This minimizes total loss exposure - sell early!
                if ytd_value > best_ytd:  # Less negative = better
                    best_ytd = ytd_value
                    best_month = month
                
                previous_ytd = ytd_value
        
        print()
        if best_month:
            best_ytd_loss = monthly_data.get(best_month, worst_entity['net_income'])
            print(f"Best Month to Sell: {best_month}")
            print(f"  YTD Loss at that point: ${best_ytd_loss:,.2f}")
            print(f"  Rationale: Sell as early as possible to minimize loss exposure")
        print()
        
        # Step 3: Estimate sale price
        print("STEP 3: Estimating Sale Price")
        print("-" * 80)
        
        # Simple valuation methods
        annual_loss = worst_entity['net_income']
        
        # Method 1: Asset-based (assume assets = 2x annual revenue/loss)
        # Method 2: Multiple of loss (negative value - pay to get rid of it)
        # Method 3: Book value estimate
        
        # Conservative estimate: Sale at book value or small premium
        # For a loss-making entity, might need to pay buyer or sell at discount
        estimated_sale_price = abs(annual_loss) * 0.5  # 50% of annual loss as sale price
        # Or might need to pay buyer to take it: -abs(annual_loss) * 0.2
        
        print(f"Entity Annual Loss: ${abs(annual_loss):,.2f}")
        print()
        print("Valuation Scenarios:")
        print(f"  Scenario 1 (Asset Sale): ${estimated_sale_price:,.2f}")
        print(f"  Scenario 2 (Pay to Divest): -${abs(annual_loss) * 0.2:,.2f}")
        print(f"  Scenario 3 (Break-even): $0.00")
        print()
        print(f"Recommended Sale Price: ${estimated_sale_price:,.2f}")
        print("  (Assumes buyer takes on assets and some liabilities)")
        print()
        
        # Step 4: Simulate impact on consolidated group
        print("STEP 4: Simulating Impact on Consolidated Group")
        print("-" * 80)
        
        # Get current consolidated results
        consolidated_result = await get_ytd_performance("FCCS_Total Geography", "FY25")
        
        if consolidated_result is None:
            print("[WARNING] Could not get consolidated results")
            await close_agent()
            return
        
        current_consolidated = consolidated_result
        entity_loss = worst_entity['net_income']
        
        # Calculate impact
        # If selling in best month, use YTD loss at that month
        if best_month and best_month in monthly_data:
            loss_removed = monthly_data[best_month]  # YTD loss at best month
        else:
            loss_removed = entity_loss  # Full year loss
        
        # New consolidated = current - entity loss + sale proceeds
        sale_proceeds = estimated_sale_price
        new_consolidated = current_consolidated - loss_removed + sale_proceeds
        
        improvement = new_consolidated - current_consolidated
        
        print(f"Current Consolidated Net Income (FY25 YTD): ${current_consolidated:,.2f}")
        print(f"Entity Loss to Remove: ${loss_removed:,.2f}")
        print(f"Estimated Sale Proceeds: ${sale_proceeds:,.2f}")
        print()
        print("=" * 80)
        print("DIVESTITURE IMPACT SIMULATION")
        print("=" * 80)
        print(f"{'Metric':<40} {'Amount':>20}")
        print("-" * 80)
        print(f"{'Current Consolidated Net Income':<40} ${current_consolidated:>19,.2f}")
        print(f"{'Entity Loss Removed':<40} ${loss_removed:>19,.2f}")
        print(f"{'Sale Proceeds':<40} ${sale_proceeds:>19,.2f}")
        print("-" * 80)
        print(f"{'New Consolidated Net Income':<40} ${new_consolidated:>19,.2f}")
        print(f"{'Improvement':<40} ${improvement:>19,.2f}")
        print("=" * 80)
        print()
        
        # Calculate percentage improvement
        if current_consolidated != 0:
            pct_improvement = (improvement / abs(current_consolidated)) * 100
            print(f"Percentage Improvement: {pct_improvement:.1f}%")
        
        print()
        print("RECOMMENDATION:")
        print(f"  - Divest: {worst_entity['entity']}")
        print(f"  - Best Month: {best_month if best_month else 'N/A'}")
        print(f"  - Sale Price: ${estimated_sale_price:,.2f}")
        print(f"  - Expected Improvement: ${improvement:,.2f}")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(simulate_divestiture())

