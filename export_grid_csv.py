"""Export FCCS grid data to CSV format with proper handling of multiple entities and accounts."""

import asyncio
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import export_data_slice


async def export_grid_to_csv(
    scenario: str = "Actual",
    year: str = "FY25",
    period: str = "Dec",
    entities: List[str] = None,
    accounts: List[str] = None,
    output_file: str = "grid_export.csv"
) -> None:
    """
    Export a grid from FCCS and save to CSV.
    
    Args:
        scenario: Scenario member (e.g., 'Actual')
        year: Year member (e.g., 'FY25')
        period: Period member (e.g., 'Dec')
        entities: List of entity member names
        accounts: List of account member names
        output_file: Output CSV file path
    """
    if entities is None:
        entities = ["FCCS_Total Geography"]
    if accounts is None:
        accounts = ["FCCS_Net Income", "40000", "FCCS_Sales"]
    
    print("=" * 80)
    print("FCCS GRID EXPORT TO CSV")
    print("=" * 80)
    print(f"Scenario: {scenario}")
    print(f"Year: {year}")
    print(f"Period: {period}")
    print(f"Entities: {entities}")
    print(f"Accounts: {accounts}")
    print(f"Output: {output_file}")
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        all_data = []
        
        # Export data for each entity-account combination
        for entity in entities:
            for account in accounts:
                # Build grid definition for single entity-account
                grid_definition = {
                    "suppressMissingBlocks": True,
                    "pov": {
                        "members": [
                            [year], [scenario], ["FCCS_YTD"], ["FCCS_Entity Total"],
                            ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                            ["FCCS_Mvmts_Total"], [entity], ["Entity Currency"],
                            ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                            ["Total Custom 4"]
                        ]
                    },
                    "columns": [{"members": [[period]]}],
                    "rows": [{"members": [[account]]}]
                }
                
                print(f"Querying: {entity} / {account}...", end=" ")
                try:
                    result = await export_data_slice(grid_definition, "Consol")
                    
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        rows_data = data.get("rows", [])
                        
                        if rows_data and len(rows_data) > 0:
                            row_data = rows_data[0].get("data", [])
                            value = row_data[0] if row_data and len(row_data) > 0 else None
                            
                            all_data.append({
                                "Entity": entity,
                                "Account": account,
                                "Period": period,
                                "Value": value
                            })
                            print(f"[OK] {value if value is not None else 'No data'}")
                        else:
                            all_data.append({
                                "Entity": entity,
                                "Account": account,
                                "Period": period,
                                "Value": None
                            })
                            print("[NO DATA]")
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"[ERROR] {error}")
                        all_data.append({
                            "Entity": entity,
                            "Account": account,
                            "Period": period,
                            "Value": None
                        })
                except Exception as e:
                    print(f"[ERROR] {str(e)}")
                    all_data.append({
                        "Entity": entity,
                        "Account": account,
                        "Period": period,
                        "Value": None
                    })
        
        # Write to CSV file
        if all_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ["Entity", "Account", "Period", "Value"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
            
            print()
            print("=" * 80)
            print(f"[OK] Exported {len(all_data)} rows to {output_file}")
            print()
            print("Sample data:")
            for row in all_data[:5]:
                print(f"  {row['Entity']:30s} | {row['Account']:30s} | {row['Period']:6s} | {row['Value']}")
            if len(all_data) > 5:
                print(f"  ... and {len(all_data) - 5} more rows")
        else:
            print("[ERROR] No data to export")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    # Example: Export grid with multiple entities and accounts
    asyncio.run(export_grid_to_csv(
        scenario="Actual",
        year="FY25",
        period="Dec",
        entities=["FCCS_Total Geography", "Industrial Segment", "Phoenix - Consolidated"],
        accounts=["FCCS_Net Income", "40000", "FCCS_Sales"],
        output_file="grid_export.csv"
    ))







