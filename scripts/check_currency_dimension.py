"""Check Currency dimension members and structure."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.client.fccs_client import FccsClient


async def check_currency_dimension():
    """Check Currency dimension members."""
    print("=" * 80)
    print("CURRENCY DIMENSION CHECK")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        client = FccsClient(config)
        app_name = "Consol"  # Application name
        
        # Check if Currency dimension exists
        print("Checking for Currency dimension...")
        print()
        
        try:
            # Try to get members of Currency dimension
            currency_members = await client.get_members(app_name, "Currency")
            
            print(f"Found Currency dimension with {len(currency_members.get('items', []))} members")
            print()
            print("Currency Members:")
            print("-" * 80)
            
            for member in currency_members.get("items", [])[:50]:  # Show first 50
                name = member.get("name", "N/A")
                parent = member.get("parent", "N/A")
                desc = member.get("description", "")
                alias = member.get("alias", "")
                
                print(f"  {name:30s} | Parent: {parent:30s} | {desc}")
            
            if len(currency_members.get("items", [])) > 50:
                print(f"\n  ... and {len(currency_members.get('items', [])) - 50} more members")
            
            print()
            print("-" * 80)
            
            # Look for specific currency-related members
            print("\nSearching for key currency members...")
            print()
            
            key_currencies = ["Entity Currency", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
            found_currencies = []
            
            for member in currency_members.get("items", []):
                name = member.get("name", "")
                if any(key.lower() in name.lower() for key in key_currencies):
                    found_currencies.append(member)
            
            if found_currencies:
                print("Found key currency members:")
                for member in found_currencies:
                    name = member.get("name", "N/A")
                    parent = member.get("parent", "N/A")
                    print(f"  - {name:30s} (Parent: {parent})")
            else:
                print("No key currency members found in search list")
            
        except Exception as e:
            print(f"Error retrieving Currency dimension: {str(e)}")
            print("\nTrying alternative approach...")
            
            # Try to get dimension list
            try:
                dimensions = await client.get_dimensions(app_name)
                print("\nAvailable dimensions:")
                for dim in dimensions.get("items", []):
                    dim_name = dim.get("name", "N/A")
                    if "currency" in dim_name.lower() or "Currency" in dim_name:
                        print(f"  *** {dim_name} ***")
                    else:
                        print(f"  {dim_name}")
            except Exception as e2:
                print(f"Error getting dimensions: {str(e2)}")
        
        print()
        print("=" * 80)
        
        # Also check what dimension is used for currency in data queries
        print("\nChecking currency dimension usage in data queries...")
        print()
        print("In smart_retrieve, the currency dimension (position 9) is set to: 'Entity Currency'")
        print("This suggests that 'Entity Currency' is a member of the Currency dimension")
        print("that represents the entity's functional currency.")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(check_currency_dimension())

