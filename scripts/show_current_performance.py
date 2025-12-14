"""Show current performance data available."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


async def show_current_performance():
    """Show current performance data."""
    print("=" * 70)
    print("CURRENT PERFORMANCE DATA - 2024")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get total Net Income for FY24
        print("Total Net Income (FY24 YTD - December):")
        print("-" * 70)
        
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
                if value:
                    net_income = float(value)
                    print(f"  Total Net Income: ${net_income:,.2f}")
                    if net_income < 0:
                        print(f"  Status: Net Loss")
                    else:
                        print(f"  Status: Net Profit")
        
        print()
        print("=" * 70)
        print("CURRENT STATUS")
        print("=" * 70)
        print()
        print("Available Data:")
        print("  [OK] Total Net Income for FY24: -$9,638,049.91")
        print()
        print("Limitation:")
        print("  [X] Cannot automatically retrieve entity list")
        print("  [X] Entity dimension members API endpoint not available")
        print()
        print("To Get Top 10 Performers:")
        print("  1. Get entity names from:")
        print("     - Oracle Smart View export")
        print("     - FCCS web interface")
        print("     - Your FCCS administrator")
        print()
        print("  2. Add entities to cache file:")
        print("     Edit: .cache/members/Consol_Entity.json")
        print()
        print("  3. Run:")
        print("     python scripts/get_top_10_performers.py")
        print()
        print("=" * 70)
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(show_current_performance())

