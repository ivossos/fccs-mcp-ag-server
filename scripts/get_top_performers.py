"""Script to retrieve top 10 performers for 2024 based on Net Income."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent, get_client
from fccs_agent.tools.data import smart_retrieve


async def get_top_performers():
    """Get top 10 performers for 2024."""
    print("=" * 60)
    print("Top 10 Performers - 2024 (Net Income)")
    print("=" * 60)
    print()
    
    try:
        # Initialize agent
        config = load_config()
        await initialize_agent(config)
        print("[OK] Agent initialized")
        print()
        
        # Note: This is a simplified approach
        # In a real scenario, you would need to:
        # 1. Get list of all entities
        # 2. Retrieve Net Income for each entity for FY24 Dec (YTD)
        # 3. Sort and get top 10
        
        print("Note: To get top performers by entity, we need to:")
        print("  1. Retrieve the list of entities from the Entity dimension")
        print("  2. For each entity, get Net Income for FY24 Dec (YTD)")
        print("  3. Sort by value and show top 10")
        print()
        print("However, the Entity dimension members endpoint is not available.")
        print("You may need to:")
        print("  - Use a pre-defined list of entities")
        print("  - Generate a report that shows entity performance")
        print("  - Use Smart View or other Oracle tools to export entity data")
        print()
        
        # Try to get total Net Income for FY24
        print("Getting total Net Income for FY24 (Dec - YTD)...")
        result = await smart_retrieve(
            account="FCCS_Net Income",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows:
                value = rows[0].get("data", [None])[0]
                print(f"[OK] Total Net Income (FY24 YTD): ${float(value):,.2f}" if value else "No data")
            else:
                print("  No data returned")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print()
        print("=" * 60)
        print("To get entity-level performance, please:")
        print("  1. Use Oracle Smart View to export entity data")
        print("  2. Generate a custom report in FCCS")
        print("  3. Or provide a list of specific entities to query")
        print("=" * 60)
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(get_top_performers())

