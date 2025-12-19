"""Get top 10 performers for 2025 - queries all entities from CSV."""

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


async def query_entity_performance(entity_name: str, year: str = "FY25") -> Optional[float]:
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


async def get_top_10_performers_2025():
    """Get top 10 performers for 2025."""
    print("=" * 70)
    print("Top 10 Performers - 2025 (Net Income - YTD)")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get total first
        print("Getting total Net Income for FY25...")
        total_result = await smart_retrieve(
            account="FCCS_Net Income",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY25",
            scenario="Actual"
        )
        
        if total_result.get("status") == "success":
            data = total_result.get("data", {})
            rows = data.get("rows", [])
            if rows:
                total_value = rows[0].get("data", [None])[0]
                if total_value:
                    print(f"Total Net Income (FY25 YTD): ${float(total_value):,.2f}")
        print()
        
        # Get entities from CSV cache
        print("Loading entities from CSV file...")
        cached_entities = load_members_from_cache("Consol", "Entity")
        
        entities_to_query = []
        
        if cached_entities and cached_entities.get("items"):
            print(f"[OK] Found {len(cached_entities['items'])} entities in CSV")
            # Filter out system entities and parent rollups
            exclude = ["FCCS_Global Assumptions", "FCCS_Total Geography", "Entity", 
                      "Industrial Segment", "Energy Segment", "Fire Protection Segment",
                      "Administrative Segment", "I/C East & West", "I/C Central"]
            entities_to_query = [
                item.get("name") for item in cached_entities["items"] 
                if item.get("name") and item.get("name") not in exclude
            ]
            print(f"Querying {len(entities_to_query)} entities (excluding system/parent entities)")
        else:
            print("[WARNING] No entity list available from CSV")
            await close_agent()
            return
        
        if not entities_to_query:
            print("No entities to query.")
            await close_agent()
            return
        
        print()
        print(f"Querying Net Income for {len(entities_to_query)} entities for FY25...")
        print("(This may take several minutes)")
        print()
        
        entity_performance = []
        queried = 0
        errors = 0
        
        for entity in entities_to_query:
            queried += 1
            if queried % 20 == 0:
                print(f"  Progress: {queried}/{len(entities_to_query)} (Found {len(entity_performance)} with data)...")
            
            value = await query_entity_performance(entity, "FY25")
            if value is not None:
                entity_performance.append({
                    "entity": entity,
                    "net_income": value
                })
            elif queried % 50 == 0:
                errors += 1
        
        print()
        print("=" * 70)
        
        if not entity_performance:
            print("No performance data retrieved.")
            print("This could mean:")
            print("  - Entities don't have data for FY25")
            print("  - Entity names don't match")
            print("  - API access issues")
        else:
            # Sort by Net Income (descending)
            entity_performance.sort(key=lambda x: x["net_income"], reverse=True)
            
            # Show top 10
            top_10 = entity_performance[:10]
            
            print("TOP 10 PERFORMERS - 2025 (Net Income YTD)")
            print("=" * 70)
            print(f"{'Rank':<6} {'Entity':<45} {'Net Income':>20}")
            print("-" * 70)
            
            for i, perf in enumerate(top_10, 1):
                entity_name = perf["entity"][:43]  # Truncate if too long
                net_income = perf["net_income"]
                print(f"{i:<6} {entity_name:<45} ${net_income:>19,.2f}")
            
            print("=" * 70)
            print(f"Total entities queried: {len(entities_to_query)}")
            print(f"Entities with data: {len(entity_performance)}")
            print(f"Top performer: {top_10[0]['entity']} with ${top_10[0]['net_income']:,.2f}")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(get_top_10_performers_2025())












