
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
    
    # Check top entities and a few others
    entities = ["FCCS_Total Geography", "Industrial Segment", "Energy Segment", "Fire Protection Segment"]
    years = ["FY24", "FY25"]
    
    print("CUMULATIVE TRANSLATION ADJUSTMENT (CTA) REPORT")
    print("=" * 60)
    
    results = []
    
    for year in years:
        print(f"\nYear: {year}")
        grid = {
            "suppressMissingBlocks": True,
            "pov": {
                "members": [
                    [year], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                    ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                    ["FCCS_Mvmts_FX_to_CTA"], ["USD"], # Probing USD currency explicitly
                    ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                    ["Total Custom 4"]
                ]
            },
            "columns": [{"members": [["Dec"]]}],
            "rows": [{"members": [[e] for e in entities]}, {"members": [["FCCS_CTA"]]}]
        }
        
        try:
            result = await _client.export_data_slice(_app_name, "Consol", grid)
            rows = result.get("rows", [])
            for i, row in enumerate(rows):
                if row.get("data") and row["data"][0] is not None:
                    val = float(row["data"][0])
                    entity = entities[i]
                    results.append({"year": year, "entity": entity, "value": val})
                    print(f"  Entity: {entity:30s} Value: ${val:15,.2f}")
        except Exception as e:
            print(f"  Error retrieving for {year}: {str(e)}")

    if not results:
        print("\nNo CTA data found for the selected years and entities.")
        print("Note: All entities in the system are currently set to USD base currency,")
        print("which results in zero translation adjustments during consolidation.")
    
    await close_agent()

if __name__ == "__main__":
    asyncio.run(run_cta_report())



