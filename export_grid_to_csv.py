"""Export FCCS grid data to CSV format."""

import asyncio
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

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
        entities = ["E1", "E2", "E3"]
    if accounts is None:
        accounts = ["A1", "A2", "A3"]
    
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
        
        # Build grid definition
        grid_definition = {
            "suppressMissingBlocks": True,
            "pov": {
                "members": [
                    [year], [scenario], ["FCCS_YTD"], ["FCCS_Entity Total"],
                    ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                    ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"], ["Entity Currency"],
                    ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                    ["Total Custom 4"]
                ]
            },
            "columns": [{"members": [[period]]}],
            "rows": [
                {"members": [[entity] for entity in entities]},
                {"members": [[account] for account in accounts]}
            ]
        }
        
        print("Exporting data slice...")
        result = await export_data_slice(grid_definition, "Consol")
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows_data = data.get("rows", [])
            columns_data = data.get("columns", [])
            
            print(f"[OK] Retrieved {len(rows_data)} rows")
            
            # Convert to CSV format
            csv_rows = []
            
            # Header row: Entity, Account, Period1, Period2, ...
            header = ["Entity", "Account"]
            if columns_data:
                for col in columns_data:
                    col_members = col.get("members", [])
                    for member_list in col_members:
                        for member in member_list:
                            header.append(str(member))
            csv_rows.append(header)
            
            # Data rows
            entity_idx = 0
            account_idx = 0
            
            for row in rows_data:
                row_data = row.get("data", [])
                row_members = row.get("members", [])
                
                # Determine which dimension this row represents
                if entity_idx < len(entities):
                    current_entity = entities[entity_idx]
                    current_account = accounts[account_idx] if account_idx < len(accounts) else ""
                    
                    # Create CSV row
                    csv_row = [current_entity, current_account]
                    csv_row.extend([str(val) if val is not None else "" for val in row_data])
                    csv_rows.append(csv_row)
                    
                    # Update indices
                    account_idx += 1
                    if account_idx >= len(accounts):
                        account_idx = 0
                        entity_idx += 1
                else:
                    # Handle remaining rows
                    current_account = accounts[account_idx] if account_idx < len(accounts) else ""
                    csv_row = ["", current_account]
                    csv_row.extend([str(val) if val is not None else "" for val in row_data])
                    csv_rows.append(csv_row)
                    account_idx += 1
            
            # Write to CSV file
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_rows)
            
            print(f"[OK] Exported to {output_file}")
            print(f"     Total rows: {len(csv_rows) - 1} (excluding header)")
            print()
            print("First few rows:")
            for i, row in enumerate(csv_rows[:min(6, len(csv_rows))]):
                print(f"  {row}")
            
        else:
            error = result.get("error", "Unknown error")
            print(f"[ERROR] Export failed: {error}")
            print()
            print("Possible reasons:")
            print("  - Member names don't exist in FCCS")
            print("  - Invalid grid definition structure")
            print("  - API connection issue")
            print()
            print("Note: E1, E2, E3 and A1, A2, A3 are placeholder names.")
            print("      Replace them with actual member names from your FCCS application.")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    # Example usage with placeholder names
    # Replace with actual member names from your FCCS application
    asyncio.run(export_grid_to_csv(
        scenario="Actual",
        year="FY25",
        period="Dec",
        entities=["E1", "E2", "E3"],  # Replace with actual entity names
        accounts=["A1", "A2", "A3"],  # Replace with actual account names
        output_file="grid_export.csv"
    ))







