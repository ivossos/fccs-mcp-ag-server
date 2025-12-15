"""Get Cumulative Translation Adjustment (CTA) for 2025."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve, export_data_slice


async def get_cta_2025():
    """Get Cumulative Translation Adjustment for all periods in 2025."""
    print("=" * 70)
    print("CUMULATIVE TRANSLATION ADJUSTMENT (CTA) - 2025")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # First verify account works with FY24
        print("Verifying account name with FY24 data...")
        test_result = await smart_retrieve(
            account="FCCS_CTA",
            entity="FCCS_Total Geography",
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        if test_result.get("status") == "success":
            data = test_result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                if value is not None:
                    print(f"  FY24 Dec CTA: ${float(value):,.2f} (Account verified)")
                else:
                    print("  FY24 Dec: No data")
            else:
                print("  FY24 Dec: No data")
        else:
            print(f"  FY24 test failed: {test_result.get('error', 'Unknown')}")
        print()
        
        # Now try FY25
        print("Retrieving CTA data for FY25...")
        print()
        
        # Try using export_data_slice to get all periods at once
        print("Attempting to retrieve all periods at once...")
        periods = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        grid_definition = {
            "suppressMissingBlocks": True,
            "pov": {
                "members": [
                    ["FY25"], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                    ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                    ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"], ["Entity Currency"],
                    ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                    ["Total Custom 4"]
                ]
            },
            "columns": [{"members": [[p] for p in periods]}],
            "rows": [{"members": [["FCCS_CTA"]]}]
        }
        
        results = []
        
        try:
            slice_result = await export_data_slice(grid_definition, "Consol")
            if slice_result.get("status") == "success":
                data = slice_result.get("data", {})
                rows = data.get("rows", [])
                columns = data.get("columns", [])
                
                if rows and rows[0].get("data"):
                    values = rows[0]["data"]
                    for i, period in enumerate(periods):
                        if i < len(values) and values[i] is not None:
                            value_float = float(values[i])
                            results.append({
                                "period": period,
                                "value": value_float
                            })
                            print(f"  {period:6s}: ${value_float:>15,.2f}")
                        else:
                            print(f"  {period:6s}: No data")
                else:
                    print("  No data returned from export_data_slice")
            else:
                print(f"  Error: {slice_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  Error with export_data_slice: {str(e)}")
            print("  Falling back to individual period queries...")
            print()
            
            # Fallback: try individual periods
            for period in periods:
                try:
                    result = await smart_retrieve(
                        account="FCCS_CTA",
                        entity="FCCS_Total Geography",
                        period=period,
                        years="FY25",
                        scenario="Actual"
                    )
                    
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        rows = data.get("rows", [])
                        if rows and rows[0].get("data"):
                            value = rows[0]["data"][0]
                            if value is not None:
                                value_float = float(value)
                                results.append({
                                    "period": period,
                                    "value": value_float
                                })
                                print(f"  {period:6s}: ${value_float:>15,.2f}")
                except Exception:
                    pass
        
        print()
        print("=" * 70)
        
        if results:
            print("\nSummary:")
            print(f"  Total periods with data: {len(results)}")
            if results:
                # Find Dec (year-to-date cumulative)
                dec_data = next((r for r in results if r["period"] == "Dec"), None)
                if dec_data:
                    print(f"  Year-to-Date (Dec): ${dec_data['value']:,.2f}")
                else:
                    last_period = results[-1]
                    print(f"  Last Period ({last_period['period']}): ${last_period['value']:,.2f}")
                
                # Show cumulative progression if we have multiple periods
                if len(results) > 1:
                    print("\n  Cumulative Translation Adjustment by Period:")
                    for r in results:
                        print(f"    {r['period']:6s}: ${r['value']:>15,.2f}")
        else:
            print("\nNo data found for CTA in FY25")
            print("\nNote: The account 'FCCS_CTA' exists in the system but contains no data.")
            print("This could mean:")
            print("  - Data has not been loaded for FY25")
            print("  - Translation adjustments have not been calculated")
            print("  - The account may need different dimension settings")
        
        print()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(get_cta_2025())

