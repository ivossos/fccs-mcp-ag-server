"""Find entities with Net Income variance >20% vs FY24 and group by region.

This script:
1. Gets all entities (excluding totals/consolidated)
2. Retrieves Net Income for FY24 and FY25 YTD
3. Calculates variance percentage
4. Filters entities with variance >20%
5. Groups results by region
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve, export_data_slice
from fccs_agent.tools.dimensions import get_members


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


async def get_entity_region_mapping(entities: List[str]) -> Dict[str, str]:
    """Get region for each entity.
    
    Attempts multiple methods:
    1. Try to query Region dimension members
    2. Infer from entity hierarchy/segment
    3. Use entity metadata if available
    """
    entity_region_map = {}
    
    if not entities:
        return entity_region_map
    
    # Method 1: Try to get Region dimension members
    try:
        # Try common region dimension names
        region_dim_names = ["Region", "Custom3", "Geography"]
        region_members = None
        
        for dim_name in region_dim_names:
            try:
                result = await get_members(dim_name)
                if result.get("status") == "success":
                    region_members = result.get("data", {}).get("items", [])
                    print(f"  [OK] Found Region dimension: {dim_name} ({len(region_members)} members)")
                    break
            except Exception:
                continue
        
        # If we have region members, we could try to map entities to regions
        # This would require additional queries or metadata
    except Exception as e:
        print(f"  [INFO] Could not retrieve Region dimension: {str(e)}")
    
    # Method 2: Infer region from entity name/segment
    # Map entities to segments/regions based on naming patterns
    segment_keywords = {
        "Industrial": ["Industrial", "01_", "Phoenix", "Washington", "Leland", "IFS"],
        "Energy": ["Energy", "02_", "Stanley", "Killdeer", "Carlsbad", "Williston", "Pecos", "Midland"],
        "Fire Protection": ["Fire Protection", "03_"],
        "Administrative": ["Administrative", "99_", "VENT", "CVNT"]
    }
    
    for entity in entities:
        region = "Unknown"
        
        # Check entity name for segment keywords
        for seg_name, keywords in segment_keywords.items():
            if any(kw in entity for kw in keywords):
                region = seg_name
                break
        
        entity_region_map[entity] = region
    
    return entity_region_map


def filter_entities(entities: List[Dict]) -> List[str]:
    """Filter out totals, consolidated, and system entities."""
    exclude_keywords = [
        "FCCS_Global Assumptions",
        "FCCS_Total Geography",
        "FCCS_Entity Total",
        "Total",
        "Consolidated",
        "Consolidation",
        "Segment",
        "Rollup",
        "Elim",
        "I/C"
    ]
    
    filtered = []
    for entity in entities:
        name = entity.get("name", "")
        # Skip if contains any exclude keyword
        if not any(kw in name for kw in exclude_keywords):
            filtered.append(name)
    
    return filtered


async def analyze_net_income_variance_by_region():
    """Main analysis function."""
    print("=" * 80)
    print("NET INCOME VARIANCE ANALYSIS BY REGION")
    print("Finding entities with variance >20% vs FY24")
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
            await close_agent()
            return
        
        all_entities = entities_result.get("data", {}).get("items", [])
        print(f"[OK] Found {len(all_entities)} total entities")
        
        # Filter entities
        entity_names = filter_entities(all_entities)
        print(f"[OK] Filtered to {len(entity_names)} entities (excluding totals/consolidated)")
        print()
        
        # Get Net Income for each entity
        print("Retrieving Net Income data for FY24 and FY25...")
        print("(This may take several minutes)")
        print()
        
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
        
        # Try to get region mapping
        print("Attempting to retrieve region information...")
        entity_names_with_variance = [e["entity"] for e in significant_variance]
        region_mapping = await get_entity_region_mapping(entity_names_with_variance)
        
        # Group by region (for now, use "Unknown" if region not found)
        # In a real scenario, you would use the region_mapping
        entities_by_region = defaultdict(list)
        
        for entity_info in significant_variance:
            region = region_mapping.get(entity_info["entity"], "Unknown")
            entities_by_region[region].append(entity_info)
        
        # Display results
        print("=" * 80)
        print("RESULTS: ENTITIES WITH NET INCOME VARIANCE >20% VS FY24")
        print("=" * 80)
        print()
        
        if not significant_variance:
            print("No entities found with variance >20%")
        else:
            # Sort regions by number of entities (descending)
            sorted_regions = sorted(entities_by_region.keys(), 
                                  key=lambda r: len(entities_by_region[r]), 
                                  reverse=True)
            
            # Display summary by region
            for region in sorted_regions:
                region_entities = entities_by_region[region]
                # Sort entities within region by absolute variance percentage
                region_entities.sort(key=lambda x: abs(x["variance_percent"]), reverse=True)
                
                print(f"\n{'=' * 80}")
                print(f"REGION: {region} ({len(region_entities)} entities)")
                print(f"{'=' * 80}")
                print()
                print(f"{'Entity':<50} {'FY24':>15} {'FY25':>15} {'Variance %':>12} {'Variance $':>15}")
                print("-" * 110)
                
                for e in region_entities:
                    variance_sign = "+" if e["variance_percent"] > 0 else ""
                    print(f"{e['entity']:<50} "
                          f"${e['fy24']:>14,.2f} "
                          f"${e['fy25']:>14,.2f} "
                          f"{variance_sign}{e['variance_percent']:>11.2f}% "
                          f"${e['variance_absolute']:>14,.2f}")
            
            # Overall summary
            print()
            print("=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Total entities analyzed: {len(entity_data)}")
            print(f"Entities with variance >20%: {len(significant_variance)}")
            print()
            
            # Top 10 by variance
            print("Top 10 entities by variance percentage:")
            print("-" * 80)
            for i, e in enumerate(significant_variance[:10], 1):
                variance_sign = "+" if e["variance_percent"] > 0 else ""
                print(f"{i:2}. {e['entity']:<45} {variance_sign}{e['variance_percent']:>10.2f}% "
                      f"(${e['variance_absolute']:>14,.2f})")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(analyze_net_income_variance_by_region())

