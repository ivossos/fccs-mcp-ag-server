"""Check what currencies are used in the FCCS application."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import export_data_slice
from fccs_agent.tools.dimensions import get_dimensions, get_members

# Common currency codes to test
COMMON_CURRENCIES = [
    "USD", "EUR", "GBP", "BRL", "CAD", "MXN", "JPY", "CNY", "AUD", "INR",
    "CHF", "SGD", "HKD", "NZD", "ZAR", "SEK", "NOK", "DKK", "PLN", "CZK",
    "Entity Currency", "FCCS_Entity Currency", "Local Currency", "Base Currency",
    "Reporting Currency", "USD_Entity Currency"
]


async def check_currencies():
    """Check what currencies are used in the application."""
    print("=" * 70)
    print("CHECKING CURRENCIES USED IN FCCS APPLICATION")
    print("=" * 70)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # First, check all available dimensions
        print("1. Checking available dimensions...")
        dims_result = await get_dimensions()
        if dims_result.get("status") == "success":
            dimensions = dims_result.get("data", {}).get("items", [])
            print(f"   Found {len(dimensions)} dimensions:")
            for dim in dimensions:
                print(f"     - {dim.get('name')} ({dim.get('type')})")
            
            # Check if there's a Currency dimension with a different name
            currency_related = [d for d in dimensions if 'currency' in d.get('name', '').lower() or 'curr' in d.get('name', '').lower()]
            if currency_related:
                print(f"\n   Found currency-related dimensions: {[d.get('name') for d in currency_related]}")
        print()
        
        # Try to get members for dimensions that might contain currencies
        print("2. Checking dimension members that might contain currencies...")
        dimension_names_to_check = ["Currency", "Curr", "View", "Consolidation"]
        
        for dim_name in dimension_names_to_check:
            try:
                result = await get_members(dim_name)
                if result.get("status") == "success":
                    data = result.get("data", {})
                    items = data.get("items", [])
                    if items:
                        print(f"\n   {dim_name} dimension members ({len(items)} found):")
                        # Show first 20 members
                        for item in items[:20]:
                            name = item.get("name", "Unknown")
                            print(f"     - {name}")
                        if len(items) > 20:
                            print(f"     ... and {len(items) - 20} more")
            except Exception as e:
                # Dimension might not exist, skip
                pass
        print()
        
        # Check entity metadata CSV for currency information
        print("3. Checking entity metadata for currency information...")
        entity_csv = Path(__file__).parent.parent / "Ravi_ExportedMetadata_Entity.csv"
        currencies_found = set()
        entity_currency_count = {}
        
        if entity_csv.exists():
            import csv
            try:
                with open(entity_csv, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    
                    # Look for currency-related columns
                    currency_columns = [h for h in (headers or []) if 'currency' in h.lower() or 'curr' in h.lower()]
                    if currency_columns:
                        print(f"   Found currency column: {currency_columns[0]}")
                        # Read all rows to get all currencies
                        for row in reader:
                            for col in currency_columns:
                                value = row.get(col, "").strip()
                                if value and value != "<none>":
                                    currencies_found.add(value)
                                    entity_name = row.get("Entity", "").strip()
                                    if entity_name:
                                        entity_currency_count[value] = entity_currency_count.get(value, 0) + 1
                        
                        if currencies_found:
                            print(f"\n   Currencies used in the application ({len(currencies_found)} found):")
                            print()
                            for curr in sorted(currencies_found):
                                count = entity_currency_count.get(curr, 0)
                                print(f"     {curr:10s} - Used by {count:3d} entities")
                        else:
                            print("   No currencies found in entity metadata")
                    else:
                        print("   No currency columns found in entity metadata")
            except Exception as e:
                print(f"   Error reading entity CSV: {e}")
        else:
            print("   Entity metadata CSV not found")
        print()
        
        # Try to test common currency codes by attempting data retrieval
        print("4. Testing currency codes in data exports...")
        print("   (Testing which currency values work in POV)")
        print()
        
        working_currencies = []
        
        # Test with a simple account query using different currencies
        test_account = "FCCS_Net Income"
        test_period = "Dec"
        test_year = "FY25"
        
        # Test currencies found in metadata plus common ones
        currencies_to_test = list(currencies_found) + COMMON_CURRENCIES[:15]
        currencies_to_test = list(dict.fromkeys(currencies_to_test))  # Remove duplicates
        
        for currency in currencies_to_test:
            try:
                grid_definition = {
                    "suppressMissingBlocks": True,
                    "pov": {
                        "members": [
                            [test_year], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                            ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                            ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"], [currency],
                            ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                            ["Total Custom 4"]
                        ]
                    },
                    "columns": [{"members": [[test_period]]}],
                    "rows": [{"members": [[test_account]]}]
                }
                
                result = await export_data_slice(grid_definition, "Consol")
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rows = data.get("rows", [])
                    if rows and rows[0].get("data"):
                        value = rows[0]["data"][0]
                        if value is not None:
                            working_currencies.append(currency)
                            print(f"   ✓ {currency:25s} - Works (has data)")
                        else:
                            print(f"   ? {currency:25s} - Accepted but no data")
                    else:
                        print(f"   ? {currency:25s} - Accepted but empty response")
                else:
                    error = result.get("error", "")
                    # Only show non-standard errors
                    if "400" not in str(error) and "404" not in str(error) and "Bad Request" not in str(error):
                        print(f"   ? {currency:25s} - {str(error)[:40]}")
            except Exception as e:
                # Skip errors for individual currencies
                pass
        
        print()
        print("=" * 70)
        print("\nSUMMARY")
        print("=" * 70)
        
        if currencies_found:
            print(f"\n[OK] Currencies Used in the Application: {len(currencies_found)}")
            print()
            for curr in sorted(currencies_found):
                count = entity_currency_count.get(curr, 0)
                percentage = (count / sum(entity_currency_count.values()) * 100) if entity_currency_count else 0
                print(f"  {curr:10s} - {count:3d} entities ({percentage:.1f}%)")
        else:
            print("\n[WARNING] No currencies found in entity metadata")
        
        print()
        print("Note: In FCCS data exports, 'Entity Currency' is used in the POV")
        print("      to represent each entity's local/base currency.")
        print()
        
        if working_currencies:
            print(f"[OK] Currency codes that work in data queries: {len(working_currencies)}")
            for curr in working_currencies:
                print(f"  - {curr}")
        print()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(check_currencies())

