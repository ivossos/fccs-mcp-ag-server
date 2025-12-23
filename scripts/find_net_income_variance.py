"""Find entities with Net Income variance >20% vs FY24.

This script retrieves Net Income for all entities and identifies those with >20% variance.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.tools.dimensions import get_members


# Entities to exclude (consolidated/total entities)
EXCLUDED_ENTITIES = {
    "FCCS_Total Geography",
    "FCCS_Global Assumptions",
    "Industrial Segment",
    "Energy Segment",
    "Fire Protection Segment",
    "Administrative Segment",
    "Industrial Consolidated Corp",
    "Energy Consolidated Corp",
    "Monumental Rollup",
    "Total Monumental",
    "Total MSC",
    "Elim",
    "I/C East & West",
    "I/C Central"
}


async def get_net_income_value(entity: str, year: str) -> Optional[float]:
    """Get Net Income YTD (Dec) for an entity."""
    try:
        result = await smart_retrieve(
            account="FCCS_Net Income",
            entity=entity,
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
        print(f"  [ERROR] Failed to retrieve {year} data for {entity}: {str(e)}")
    return None


async def find_entities_with_variance():
    """Find all entities with Net Income variance >20% vs FY24."""
    
    print("=" * 80)
    print("FINDING ENTITIES WITH NET INCOME VARIANCE >20% VS FY24")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get all entities
        print("Retrieving entity list...")
        entities_result = await get_members("Entity")
        
        if entities_result.get("status") != "success":
            print("[ERROR] Failed to retrieve entities")
            return
        
        all_entities = entities_result.get("data", {}).get("items", [])
        entity_names = [e["name"] for e in all_entities if e["name"] not in EXCLUDED_ENTITIES]
        
        print(f"[OK] Found {len(entity_names)} individual entities (excluding totals/consolidated)")
        print()
        
        # Get Net Income for each entity
        print("Retrieving Net Income data for FY24 and FY25...")
        entity_data = []
        processed = 0
        
        for entity in entity_names:
            processed += 1
            if processed % 50 == 0:
                print(f"  Processed {processed}/{len(entity_names)} entities...")
            
            fy24_value = await get_net_income_value(entity, "FY24")
            fy25_value = await get_net_income_value(entity, "FY25")
            
            # Calculate variance if both values exist
            if fy24_value is not None and fy25_value is not None:
                variance_absolute = fy25_value - fy24_value
                
                # Calculate percentage variance
                if fy24_value != 0:
                    variance_percent = (variance_absolute / abs(fy24_value)) * 100
                else:
                    variance_percent = float('inf') if variance_absolute > 0 else (float('-inf') if variance_absolute < 0 else 0)
                
                entity_data.append({
                    "entity": entity,
                    "fy24": fy24_value,
                    "fy25": fy25_value,
                    "variance_absolute": variance_absolute,
                    "variance_percent": variance_percent
                })
        
        print(f"[OK] Retrieved data for {len(entity_data)} entities with both FY24 and FY25 data")
        print()
        
        # Filter entities with variance >20%
        print("Filtering entities with variance >20%...")
        significant_variance = [
            e for e in entity_data 
            if abs(e["variance_percent"]) > 20 and not (abs(e["variance_percent"]) == float('inf'))
        ]
        
        print(f"[OK] Found {len(significant_variance)} entities with variance >20%")
        print()
        
        # Sort by absolute variance percentage
        significant_variance.sort(key=lambda x: abs(x["variance_percent"]), reverse=True)
        
        # Display results
        print("=" * 80)
        print("RESULTS: ENTITIES WITH NET INCOME VARIANCE >20% VS FY24")
        print("=" * 80)
        print()
        print(f"{'Rank':<6} {'Entity':<50} {'FY24':>15} {'FY25':>15} {'Variance $':>15} {'Variance %':>12}")
        print("-" * 113)
        
        for rank, entity_info in enumerate(significant_variance, 1):
            entity = entity_info["entity"]
            fy24 = entity_info["fy24"]
            fy25 = entity_info["fy25"]
            var_abs = entity_info["variance_absolute"]
            var_pct = entity_info["variance_percent"]
            
            # Format variance percentage with sign
            var_pct_str = f"{var_pct:+.1f}%"
            
            print(f"{rank:<6} {entity:<50} ${fy24:>14,.2f} ${fy25:>14,.2f} ${var_abs:>14,.2f} {var_pct_str:>12}")
        
        print()
        print("=" * 80)
        print(f"Total entities analyzed: {len(entity_data)}")
        print(f"Entities with variance >20%: {len(significant_variance)}")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(find_entities_with_variance())



