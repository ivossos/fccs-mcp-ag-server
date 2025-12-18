"""Comprehensive Entity Analysis - List apps, connect, show top/underperformers, and simulate divestment."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.application import get_application_info
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache
import csv


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
    except Exception as e:
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


async def comprehensive_analysis():
    """Run comprehensive entity analysis."""
    print("=" * 80)
    print("COMPREHENSIVE ENTITY ANALYSIS")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Step 1: List all FCCS apps
        print("=" * 80)
        print("STEP 1: LISTING ALL FCCS APPS")
        print("=" * 80)
        print()
        
        app_info = await get_application_info()
        if app_info.get("status") == "success":
            apps_data = app_info.get("data", {})
            apps = apps_data.get("items", [])
            
            if apps:
                print(f"Found {len(apps)} application(s):")
                print()
                for i, app in enumerate(apps, 1):
                    app_name = app.get("name", "Unknown")
                    app_type = app.get("type", "Unknown")
                    print(f"  {i}. {app_name} (Type: {app_type})")
                
                # Check if "Consol" app exists
                consol_app = None
                for app in apps:
                    app_name = app.get("name", "")
                    if "Consol" in app_name or "consol" in app_name.lower():
                        consol_app = app_name
                        break
                
                if consol_app:
                    print()
                    print(f"[OK] Found 'Consol' app: {consol_app}")
                else:
                    print()
                    print("[INFO] No app with 'Consol' in name found.")
                    if apps:
                        print(f"[INFO] Using first available app: {apps[0].get('name')}")
            else:
                print("[WARNING] No applications found")
        else:
            print("[ERROR] Failed to retrieve application info")
        
        print()
        print("=" * 80)
        print("STEP 2: CONNECTED TO CONSOL APP")
        print("=" * 80)
        print()
        print("[OK] Connection established (app name set during initialization)")
        print()
        
        # Step 3: Top 10 performing entities for actuals 2024
        print("=" * 80)
        print("STEP 3: TOP 10 PERFORMING ENTITIES - ACTUALS 2024")
        print("=" * 80)
        print()
        
        # Get total first
        print("Getting total Net Income for FY24...")
        total_result = await smart_retrieve(
            account="FCCS_Net Income",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        if total_result.get("status") == "success":
            data = total_result.get("data", {})
            rows = data.get("rows", [])
            if rows:
                total_value = rows[0].get("data", [None])[0]
                if total_value:
                    print(f"Total Net Income (FY24 YTD): ${float(total_value):,.2f}")
        print()
        
        # Get entities from cache
        print("Checking for cached Entity members...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        entity_alias_map = {}  # Map entity name to alias/description
        
        if cached_entities and cached_entities.get("items"):
            print(f"[OK] Found {len(cached_entities['items'])} entities in cache")
            for item in cached_entities["items"]:
                entity_name = item.get("name")
                if entity_name:
                    entities_to_query.append(entity_name)
                    # Get alias or description for display
                    alias = item.get("alias") or item.get("description") or entity_name
                    entity_alias_map[entity_name] = alias
        else:
            print("[WARNING] No entity list available in cache")
            print("  Please ensure entity cache exists at: .cache/members/Consol_Entity.json")
            await close_agent()
            return
        
        # Try to load aliases from CSV file if available
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
                                    entity_alias_map[entity_name] = alias
                        break
                    except Exception:
                        if encoding == encodings[-1]:
                            raise
                        continue
            except Exception:
                pass  # If CSV can't be read, just use cache aliases
        
        if not entities_to_query:
            print("No entities to query.")
            await close_agent()
            return
        
        # Exclude total/consolidated entities
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total", "Consolidated", "Segment"]
        individual_entities = [
            e for e in entities_to_query 
            if not any(keyword in e for keyword in exclude_keywords)
        ]
        
        print(f"Querying Net Income for {len(individual_entities)} individual entities (FY24)...")
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
        if entity_performance_2024:
            # Sort by Net Income (descending) - highest first
            entity_performance_2024.sort(key=lambda x: x["net_income"], reverse=True)
            
            # Show top 10 performers
            top_10_performers = entity_performance_2024[:10]
            
            print("TOP 10 PERFORMING ENTITIES - 2024 (Net Income YTD)")
            print("=" * 80)
            print(f"{'Rank':<6} {'Entity':<50} {'Net Income':>20}")
            print("-" * 80)
            
            for i, perf in enumerate(top_10_performers, 1):
                entity_code = perf["entity"]
                # Use alias if available, otherwise use entity code
                display_name = entity_alias_map.get(entity_code, entity_code)
                # Format: "Alias (Code)" if alias exists and is different, otherwise just the name
                if display_name != entity_code and display_name:
                    entity_name = f"{display_name} ({entity_code})"[:48]
                else:
                    entity_name = entity_code[:48]
                net_income = perf["net_income"]
                print(f"{i:<6} {entity_name:<50} ${net_income:>19,.2f}")
            
            print("=" * 80)
            print(f"Total entities queried: {len(individual_entities)}")
            print(f"Entities with data: {len(entity_performance_2024)}")
        else:
            print("[WARNING] No performance data retrieved for FY24")
        
        print()
        print("=" * 80)
        print("STEP 4: TOP 10 UNDERPERFORMING ENTITIES - ACTUALS 2024")
        print("=" * 80)
        print()
        
        if entity_performance_2024:
            # Sort by Net Income (ascending) - lowest first = worst performers
            entity_performance_2024.sort(key=lambda x: x["net_income"])
            
            # Show top 10 underperformers
            top_10_underperformers = entity_performance_2024[:10]
            
            print("TOP 10 UNDERPERFORMING ENTITIES - 2024 (Net Income YTD)")
            print("=" * 80)
            print(f"{'Rank':<6} {'Entity':<50} {'Net Income':>20}")
            print("-" * 80)
            
            for i, perf in enumerate(top_10_underperformers, 1):
                entity_code = perf["entity"]
                # Use alias if available, otherwise use entity code
                display_name = entity_alias_map.get(entity_code, entity_code)
                # Format: "Alias (Code)" if alias exists and is different, otherwise just the name
                if display_name != entity_code and display_name:
                    entity_name = f"{display_name} ({entity_code})"[:48]
                else:
                    entity_name = entity_code[:48]
                net_income = perf["net_income"]
                print(f"{i:<6} {entity_name:<50} ${net_income:>19,.2f}")
            
            print("=" * 80)
            worst_entity_2024 = top_10_underperformers[0] if top_10_underperformers else None
            print(f"Worst Performer (2024): {worst_entity_2024['entity'] if worst_entity_2024 else 'N/A'}")
        else:
            print("[WARNING] No performance data available")
            worst_entity_2024 = None
        
        print()
        print("=" * 80)
        print("STEP 5: SIMULATING DIVESTMENT - WORST PERFORMING ENTITY (MID-YEAR 2025)")
        print("=" * 80)
        print()
        
        # Get worst performer for 2025 (for divestment simulation)
        print("Identifying worst performer for FY25...")
        print()
        
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
            print("[WARNING] No FY25 performance data found")
            print("  Using worst performer from 2024 for simulation")
            worst_entity = worst_entity_2024
            worst_entity_year = "FY24"
        else:
            # Sort to find worst (lowest Net Income)
            entity_performance_2025.sort(key=lambda x: x["net_income"])
            worst_entity = entity_performance_2025[0]
            worst_entity_year = "FY25"
        
        if not worst_entity:
            print("[ERROR] No worst entity identified")
            await close_agent()
            return
        
        worst_entity_code = worst_entity['entity']
        worst_entity_display = entity_alias_map.get(worst_entity_code, worst_entity_code)
        if worst_entity_display != worst_entity_code:
            print(f"Worst Performer: {worst_entity_display} ({worst_entity_code})")
        else:
            print(f"Worst Performer: {worst_entity_code}")
        print(f"Net Income ({worst_entity_year} YTD): ${worst_entity['net_income']:,.2f}")
        print()
        
        # Get monthly performance to find mid-year (June) data
        print("Getting monthly performance data for divestment simulation...")
        monthly_data = await get_monthly_performance(worst_entity['entity'], "FY25")
        
        if not monthly_data:
            print("[WARNING] No monthly data available, using YTD data")
            monthly_data = {"Jun": worst_entity['net_income']}
        
        # Mid-year 2025 = June
        mid_year_month = "Jun"
        mid_year_loss = monthly_data.get(mid_year_month, worst_entity['net_income'])
        
        print()
        print(f"Monthly Performance (YTD values):")
        print(f"{'Month':<10} {'YTD Net Income':>20}")
        print("-" * 30)
        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]:
            if month in monthly_data:
                print(f"{month:<10} ${monthly_data[month]:>19,.2f}")
        
        print()
        print(f"Mid-Year 2025 (June) YTD Loss: ${mid_year_loss:,.2f}")
        print()
        
        # Estimate sale price
        print("Estimating Sale Price...")
        annual_loss = worst_entity['net_income']
        estimated_sale_price = abs(annual_loss) * 0.5  # 50% of annual loss as sale price
        
        print(f"Entity Annual Loss: ${abs(annual_loss):,.2f}")
        print(f"Estimated Sale Price: ${estimated_sale_price:,.2f}")
        print("  (Assumes buyer takes on assets and some liabilities)")
        print()
        
        # Step 6: Calculate impact on consolidated group
        print("=" * 80)
        print("STEP 6: CALCULATING IMPACT ON CONSOLIDATED GROUP")
        print("=" * 80)
        print()
        
        # Get current consolidated results for FY25
        consolidated_result = await query_entity_performance("FCCS_Total Geography", "FY25")
        
        if consolidated_result is None:
            print("[WARNING] Could not get FY25 consolidated results, using FY24")
            consolidated_result = await query_entity_performance("FCCS_Total Geography", "FY24")
            year_label = "FY24"
        else:
            year_label = "FY25"
        
        if consolidated_result is None:
            print("[ERROR] Could not get consolidated results")
            await close_agent()
            return
        
        current_consolidated = consolidated_result
        loss_removed = mid_year_loss  # Loss at mid-year (June)
        sale_proceeds = estimated_sale_price
        
        # New consolidated = current - entity loss + sale proceeds
        new_consolidated = current_consolidated - loss_removed + sale_proceeds
        improvement = new_consolidated - current_consolidated
        
        print("DIVESTITURE IMPACT SIMULATION")
        print("=" * 80)
        print(f"{'Metric':<50} {'Amount':>20}")
        print("-" * 80)
        print(f"{'Current Consolidated Net Income (' + year_label + ' YTD)':<50} ${current_consolidated:>19,.2f}")
        print(f"{'Entity Loss Removed (June YTD)':<50} ${loss_removed:>19,.2f}")
        print(f"{'Estimated Sale Proceeds':<50} ${sale_proceeds:>19,.2f}")
        print("-" * 80)
        print(f"{'New Consolidated Net Income':<50} ${new_consolidated:>19,.2f}")
        print(f"{'Improvement':<50} ${improvement:>19,.2f}")
        print("=" * 80)
        print()
        
        # Calculate percentage improvement
        if current_consolidated != 0:
            pct_improvement = (improvement / abs(current_consolidated)) * 100
            print(f"Percentage Improvement: {pct_improvement:.1f}%")
        
        print()
        print("=" * 80)
        print("SUMMARY & RECOMMENDATION")
        print("=" * 80)
        print()
        worst_entity_code = worst_entity['entity']
        worst_entity_display = entity_alias_map.get(worst_entity_code, worst_entity_code)
        if worst_entity_display != worst_entity_code:
            print(f"Entity to Divest: {worst_entity_display} ({worst_entity_code})")
        else:
            print(f"Entity to Divest: {worst_entity_code}")
        print(f"Divestment Date: Mid-Year 2025 (June)")
        print(f"YTD Loss at Divestment: ${mid_year_loss:,.2f}")
        print(f"Estimated Sale Price: ${estimated_sale_price:,.2f}")
        print(f"Expected Improvement: ${improvement:,.2f}")
        print()
        
        if improvement > 0:
            print("[RECOMMENDATION] Proceed with divestment")
            print(f"   The divestment would improve consolidated results by ${improvement:,.2f}")
        else:
            print("[RECOMMENDATION] Review divestment terms")
            print(f"   Current terms show a negative impact of ${abs(improvement):,.2f}")
            print("   Consider renegotiating sale price or timing")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(comprehensive_analysis())

