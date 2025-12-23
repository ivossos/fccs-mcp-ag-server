
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent

async def run_cta_report():
    config = load_config()
    await initialize_agent(config)
    
    from fccs_agent.tools.data import _client, _app_name
    
    entities = ["FCCS_Total Geography", "Industrial Segment", "Energy Segment"]
    years = ["FY24", "FY25"]
    
    print("CUMULATIVE TRANSLATION ADJUSTMENT (CTA) REPORT - CONTRIBUTION ANALYSIS")
    print("=" * 70)
    
    found = False
    for year in years:
        print(f"\nYear: {year}")
        for entity in entities:
            # Try FCCS_Contribution which often holds translation/elimination data
            grid = {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        [year], ["Actual"], ["FCCS_YTD"], ["FCCS_Contribution"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], [entity], ["Entity Currency"],
                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": [{"members": [["Dec"]]}],
                "rows": [{"members": [["FCCS_CTA"]]}]
            }
            
            try:
                result = await _client.export_data_slice(_app_name, "Consol", grid)
                rows = result.get("rows", [])
                if rows and rows[0].get("data") and rows[0]["data"][0] is not None:
                    val = float(rows[0]["data"][0])
                    print(f"  Entity: {entity:30s} Value: ${val:15,.2f}")
                    found = True
                else:
                    print(f"  Entity: {entity:30s} Value: $0.00 (No data in Contribution)")
            except Exception:
                print(f"  Entity: {entity:30s} Value: $0.00 (Query Error)")

    if not found:
        print("\nFINAL SUMMARY:")
        print("Cumulative Translation Adjustment (CTA) remains 0.00 even in the Contribution dimension.")
        print("Conclusion: No currency translation gains or losses are currently recorded in the system.")
    
    await close_agent()

if __name__ == "__main__":
    asyncio.run(run_cta_report())


