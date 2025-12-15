"""Get top 10 performers for 2024 by querying Net Income for entities."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.client.fccs_client import FccsClient
from fccs_agent.tools.data import smart_retrieve


async def get_top_performers_2024():
    """Get top 10 performers for 2024."""
    print("=" * 60)
    print("Top 10 Performers - 2024 (Net Income)")
    print("=" * 60)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        client = FccsClient(config)
        app_name = "Consol"
        
        print("[OK] Connected to FCCS")
        print()
        
        # Try to export data with Entity in rows
        print("Attempting to retrieve entity performance data...")
        print()
        
        # Try different grid definition formats
        grid_defs = [
            # Format 1: Entity as row dimension
            {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        ["FY24"], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"],
                        ["Entity Currency"], ["Total Custom 3"],
                        ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": {
                    "members": [["Dec"]]
                },
                "rows": {
                    "members": [["FCCS_Net Income"], ["Entity"]]
                }
            },
            # Format 2: Entity as row, Account in POV
            {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        ["FY24"], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"],
                        ["Entity Currency"], ["Total Custom 3"],
                        ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"], ["FCCS_Net Income"]
                    ]
                },
                "columns": {
                    "members": [["Dec"]]
                },
                "rows": {
                    "members": [["Entity"]]
                }
            }
        ]
        
        for i, grid_def in enumerate(grid_defs, 1):
            print(f"Trying format {i}...", end=" ")
            try:
                result = await client.export_data_slice(app_name, "Consol", grid_def)
                if result:
                    print("[OK]")
                    print()
                    print("Data retrieved successfully!")
                    print(f"Result: {result}")
                    # Process and sort entities here
                    break
            except Exception as e:
                print(f"[FAILED] {str(e)[:100]}")
        
        print()
        print("=" * 60)
        print("Note: If API calls failed, you may need to:")
        print("  1. Provide a list of specific entity names to query")
        print("  2. Use Oracle Smart View to export entity data")
        print("  3. Generate a report in FCCS that shows entity performance")
        print("=" * 60)
        
        await client.close()
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(get_top_performers_2024())


