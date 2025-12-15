"""Try to query common entity name patterns to find actual entities."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve

# Common entity name patterns to try
COMMON_ENTITY_PATTERNS = [
    # Geographic patterns
    "North America", "South America", "Europe", "Asia", "Asia Pacific", "APAC",
    "EMEA", "Americas", "Latin America", "Middle East", "Africa",
    # Company/Division patterns
    "Corporate", "HQ", "Headquarters", "Parent", "Subsidiary",
    # Regional patterns
    "US", "USA", "United States", "Canada", "Mexico", "Brazil",
    "UK", "United Kingdom", "Germany", "France", "Italy", "Spain",
    "China", "Japan", "India", "Australia", "Singapore",
    # Business unit patterns
    "Division1", "Division2", "BU1", "BU2", "Business Unit 1",
    # Custom patterns (common in FCCS)
    "FCCS_No Entity", "FCCS_No Parent", "FCCS_No Consolidation",
    # Try with common prefixes/suffixes
    "Entity_001", "Entity_002", "Entity1", "Entity2",
    "Company1", "Company2", "Corp1", "Corp2"
]


async def try_common_entities():
    """Try to query common entity patterns."""
    print("=" * 70)
    print("Trying Common Entity Name Patterns")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        print(f"Trying {len(COMMON_ENTITY_PATTERNS)} common entity name patterns...")
        print("(This will test which entities exist in your system)")
        print()
        
        found_entities = []
        
        for i, entity_name in enumerate(COMMON_ENTITY_PATTERNS, 1):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(COMMON_ENTITY_PATTERNS)}...")
            
            try:
                result = await smart_retrieve(
                    account="FCCS_Net Income",
                    entity=entity_name,
                    period="Dec",
                    years="FY24",
                    scenario="Actual"
                )
                
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rows = data.get("rows", [])
                    if rows and rows[0].get("data"):
                        value = rows[0]["data"][0]
                        if value is not None:
                            found_entities.append({
                                "name": entity_name,
                                "net_income": float(value)
                            })
                            print(f"  [FOUND] {entity_name}: ${float(value):,.2f}")
            except Exception:
                # Entity doesn't exist or error - skip
                pass
        
        print()
        print("=" * 70)
        
        if found_entities:
            print(f"Found {len(found_entities)} entities with data:")
            print()
            # Sort by Net Income
            found_entities.sort(key=lambda x: x["net_income"], reverse=True)
            
            print(f"{'Rank':<6} {'Entity':<40} {'Net Income':>20}")
            print("-" * 70)
            
            for i, entity in enumerate(found_entities[:20], 1):  # Show top 20
                entity_name = entity["name"][:38]
                net_income = entity["net_income"]
                print(f"{i:<6} {entity_name:<40} ${net_income:>19,.2f}")
            
            print()
            print("=" * 70)
            print("TOP 10 PERFORMERS:")
            print("-" * 70)
            for i, entity in enumerate(found_entities[:10], 1):
                print(f"{i}. {entity['name']}: ${entity['net_income']:,.2f}")
        else:
            print("No entities found with these common patterns.")
            print()
            print("You may need to:")
            print("  1. Get entity names from Oracle Smart View")
            print("  2. Check FCCS web interface for entity list")
            print("  3. Export entity metadata from FCCS")
            print("  4. Manually add entity names to .cache/members/Consol_Entity.json")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(try_common_entities())


