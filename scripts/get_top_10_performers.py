"""Get top 10 performers for 2024 - queries specific entities or uses cached data."""

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
        print(f"  Error querying {entity_name}: {e}")
    return None


async def get_top_10_performers_2024(entity_list: Optional[list[str]] = None):
    """Get top 10 performers for 2024."""
    print("=" * 70)
    print("Top 10 Performers - 2024 (Net Income - YTD)")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
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
        
        # Try to get entities from cache
        print("Checking for cached Entity members...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        
        if cached_entities and cached_entities.get("items"):
            print(f"[OK] Found {len(cached_entities['items'])} entities in cache")
            entities_to_query = [item.get("name") for item in cached_entities["items"] if item.get("name")]
        elif entity_list:
            print(f"Using provided entity list: {len(entity_list)} entities")
            entities_to_query = entity_list
        else:
            print("[WARNING] No entity list available")
            print()
            print("Options:")
            print("  1. Create a cache file: .cache/members/Consol_Entity.json")
            print("  2. Provide entity names as a list")
            print("  3. Use Oracle Smart View to export entity data")
            print()
            await close_agent()
            return
        
        if not entities_to_query:
            print("No entities to query.")
            await close_agent()
            return
        
        print()
        print(f"Querying Net Income for {len(entities_to_query)} entities...")
        print("(This may take a while)")
        print()
        
        entity_performance = []
        queried = 0
        
        for entity in entities_to_query:
            queried += 1
            if queried % 10 == 0:
                print(f"  Progress: {queried}/{len(entities_to_query)}...")
            
            value = await query_entity_performance(entity, "FY24")
            if value is not None:
                entity_performance.append({
                    "entity": entity,
                    "net_income": value
                })
        
        print()
        print("=" * 70)
        
        if not entity_performance:
            print("No performance data retrieved.")
            print("This could mean:")
            print("  - Entities don't have data for FY24")
            print("  - Entity names don't match")
            print("  - API access issues")
        else:
            # Sort by Net Income (descending)
            entity_performance.sort(key=lambda x: x["net_income"], reverse=True)
            
            # Show top 10
            top_10 = entity_performance[:10]
            
            print("TOP 10 PERFORMERS - 2024 (Net Income YTD)")
            print("=" * 70)
            print(f"{'Rank':<6} {'Entity':<40} {'Net Income':>20}")
            print("-" * 70)
            
            for i, perf in enumerate(top_10, 1):
                entity_name = perf["entity"][:38]  # Truncate if too long
                net_income = perf["net_income"]
                print(f"{i:<6} {entity_name:<40} ${net_income:>19,.2f}")
            
            print("=" * 70)
            print(f"Total entities queried: {len(entities_to_query)}")
            print(f"Entities with data: {len(entity_performance)}")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # You can provide entity list as command line args or modify this script
    entity_list = None
    if len(sys.argv) > 1:
        entity_list = sys.argv[1].split(",")
    
    asyncio.run(get_top_10_performers_2024(entity_list))















