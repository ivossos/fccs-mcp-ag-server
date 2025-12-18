"""Get FCCS_Net Income for Entity for FY25 YTD and summarize variances vs FY24."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


async def get_ytd_net_income(entity_name: str, year: str) -> Optional[float]:
    """Get YTD Net Income for an entity (using Dec period for YTD cumulative)."""
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
        print(f"  [ERROR] Failed to retrieve {year} data: {str(e)}")
    return None


async def analyze_net_income_variance(entity_name: str = "FCCS_Total Geography"):
    """Get Net Income for FY25 YTD and summarize variances vs FY24."""
    print("=" * 80)
    print(f"NET INCOME VARIANCE ANALYSIS - {entity_name}")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get FY25 YTD
        print(f"Retrieving FY25 YTD Net Income for {entity_name}...")
        fy25_value = await get_ytd_net_income(entity_name, "FY25")
        
        if fy25_value is not None:
            print(f"  FY25 YTD (Dec): ${fy25_value:,.2f}")
        else:
            print(f"  FY25 YTD: No data available")
        print()
        
        # Get FY24 YTD
        print(f"Retrieving FY24 YTD Net Income for {entity_name}...")
        fy24_value = await get_ytd_net_income(entity_name, "FY24")
        
        if fy24_value is not None:
            print(f"  FY24 YTD (Dec): ${fy24_value:,.2f}")
        else:
            print(f"  FY24 YTD: No data available")
        print()
        
        # Calculate and summarize variances
        print("=" * 80)
        print("VARIANCE SUMMARY")
        print("=" * 80)
        print()
        
        if fy25_value is not None and fy24_value is not None:
            # Absolute variance
            variance_absolute = fy25_value - fy24_value
            
            # Percentage variance
            if fy24_value != 0:
                variance_percent = (variance_absolute / abs(fy24_value)) * 100
            else:
                variance_percent = float('inf') if variance_absolute > 0 else (float('-inf') if variance_absolute < 0 else 0)
            
            # Determine direction
            direction = "INCREASE" if variance_absolute > 0 else "DECREASE" if variance_absolute < 0 else "NO CHANGE"
            
            print(f"FY25 YTD Net Income:     ${fy25_value:>20,.2f}")
            print(f"FY24 YTD Net Income:     ${fy24_value:>20,.2f}")
            print("-" * 80)
            print(f"Absolute Variance:       ${variance_absolute:>20,.2f} ({direction})")
            print(f"Percentage Variance:    {variance_percent:>20.2f}%")
            print()
            
            # Summary insights
            print("KEY INSIGHTS:")
            print("-" * 80)
            if abs(variance_percent) < 1:
                print(f"  • Minimal change: Net Income is relatively stable year-over-year")
            elif variance_percent > 10:
                print(f"  • Significant improvement: Net Income increased by {abs(variance_percent):.1f}%")
            elif variance_percent < -10:
                print(f"  • Significant decline: Net Income decreased by {abs(variance_percent):.1f}%")
            elif variance_percent > 0:
                print(f"  • Moderate improvement: Net Income increased by {abs(variance_percent):.1f}%")
            else:
                print(f"  • Moderate decline: Net Income decreased by {abs(variance_percent):.1f}%")
            
            if variance_absolute > 0:
                print(f"  • FY25 performance is ${abs(variance_absolute):,.2f} better than FY24")
            elif variance_absolute < 0:
                print(f"  • FY25 performance is ${abs(variance_absolute):,.2f} worse than FY24")
            else:
                print(f"  • FY25 performance matches FY24 exactly")
                
        elif fy25_value is not None and fy24_value is None:
            print(f"FY25 YTD Net Income:     ${fy25_value:>20,.2f}")
            print(f"FY24 YTD Net Income:     {'No data available':>20s}")
            print()
            print("NOTE: Cannot calculate variance - FY24 data is not available")
            
        elif fy25_value is None and fy24_value is not None:
            print(f"FY25 YTD Net Income:     {'No data available':>20s}")
            print(f"FY24 YTD Net Income:     ${fy24_value:>20,.2f}")
            print()
            print("NOTE: Cannot calculate variance - FY25 data is not available")
            
        else:
            print("ERROR: No data available for either FY25 or FY24")
            print("Please verify:")
            print("  • Entity name is correct")
            print("  • Data has been loaded for both years")
            print("  • Account 'FCCS_Net Income' exists and has data")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    # Accept entity name as command-line argument, or use default
    entity_name = sys.argv[1] if len(sys.argv) > 1 else "FCCS_Total Geography"
    asyncio.run(analyze_net_income_variance(entity_name))

