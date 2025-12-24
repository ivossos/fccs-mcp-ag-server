
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.client.fccs_client import FccsClient

async def probe_cta():
    config = load_config()
    await initialize_agent(config)
    
    # Get the client directly to build custom grids
    from fccs_agent.tools.data import _client, _app_name
    
    entities = ["FCCS_Total Geography", "Industrial Segment", "Energy Segment"]
    scenarios = ["Actual"]
    years = ["FY24", "FY25"]
    periods = ["Dec"]
    
    consol_members = ["FCCS_Entity Total", "FCCS_Contribution", "FCCS_Entity Input"]
    movement_members = ["FCCS_Mvmts_Total", "FCCS_Mvmts_FX_to_CTA", "FCCS_Mvmts_FX_Total"]
    currency_members = ["Entity Currency", "USD", "Parent Currency"]
    accounts = ["FCCS_CTA", "FCCS_CICTA", "FCCS_OR OBFXCICTA"]
    
    print(f"Probing for CTA data in application: {_app_name}")
    print("-" * 60)
    
    found_any = False
    
    for year in years:
        for entity in entities:
            print(f"\nChecking Entity: {entity}, Year: {year}")
            for account in accounts:
                for consol in consol_members:
                    for mvmt in movement_members:
                        for curr in currency_members:
                            grid = {
                                "suppressMissingBlocks": True,
                                "pov": {
                                    "members": [
                                        [year], ["Actual"], ["FCCS_YTD"], [consol],
                                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                                        [mvmt], [entity], [curr],
                                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                                        ["Total Custom 4"]
                                    ]
                                },
                                "columns": [{"members": [["Dec"]]}],
                                "rows": [{"members": [[account]]}]
                            }
                            
                            try:
                                result = await _client.export_data_slice(_app_name, "Consol", grid)
                                rows = result.get("rows", [])
                                if rows and rows[0].get("data") and rows[0]["data"][0] is not None:
                                    val = rows[0]["data"][0]
                                    print(f"  [FOUND] Acc: {account}, Consol: {consol}, Mvmt: {mvmt}, Curr: {curr} -> Value: {val}")
                                    found_any = True
                            except Exception:
                                pass
    
    if not found_any:
        print("\nNo CTA data found with probed combinations.")
    
    await close_agent()

if __name__ == "__main__":
    asyncio.run(probe_cta())



