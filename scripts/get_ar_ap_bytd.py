"""Get Accounts Receivable and Accounts Payable for BYTD Dec 2024."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve, export_data_slice
from fccs_agent.utils.cache import load_members_from_cache

# Load account names from cache first
def get_account_variations_from_cache():
    """Get AR and AP account variations from cache."""
    ar_variations = []
    ap_variations = []
    
    # Load Account cache
    cached_accounts = load_members_from_cache("Consol", "Account")
    if cached_accounts:
        items = cached_accounts.get("items", [])
        for item in items:
            name = item.get("name", "")
            name_lower = name.lower()
            
            # Accounts Receivable - prioritize exact matches
            if 'acct receivable' in name_lower or name == '10200':
                if name not in ar_variations:
                    ar_variations.insert(0, name)  # Insert at beginning for priority
            elif any(term in name_lower for term in ['receivable', 'ar']) and 'balance' not in name_lower:
                if name not in ar_variations:
                    ar_variations.append(name)
            
            # Accounts Payable - prioritize exact matches
            if 'acct payable' in name_lower or name == '20200':
                if name not in ap_variations:
                    ap_variations.insert(0, name)  # Insert at beginning for priority
            elif any(term in name_lower for term in ['payable', 'ap']) and 'balance' not in name_lower and 'retained' not in name_lower:
                if name not in ap_variations:
                    ap_variations.append(name)
    
    # Add common variations as fallback (prioritize known working ones)
    if not ar_variations:
        ar_variations = [
            "FCCS_Acct Receivable",
            "10200",
            "FCCS_Account Receivable",
            "Account Receivable",
            "Accounts Receivable",
        ]
    else:
        # Ensure FCCS_Acct Receivable is first if it exists
        if "FCCS_Acct Receivable" in ar_variations:
            ar_variations.remove("FCCS_Acct Receivable")
            ar_variations.insert(0, "FCCS_Acct Receivable")
    
    if not ap_variations:
        ap_variations = [
            "FCCS_Acct Payable",
            "20200",
            "Account Payable",
            "FCCS_Account Payable",
            "Accounts Payable",
        ]
    else:
        # Ensure FCCS_Acct Payable is first if it exists
        if "FCCS_Acct Payable" in ap_variations:
            ap_variations.remove("FCCS_Acct Payable")
            ap_variations.insert(0, "FCCS_Acct Payable")
        # Remove non-AP accounts that might have matched
        ap_variations = [a for a in ap_variations if 'payable' in a.lower() or a == '20200']
    
    return ar_variations, ap_variations


async def find_and_retrieve_accounts():
    """Find and retrieve AR and AP accounts for BYTD Dec 2024."""
    print("=" * 70)
    print("ACCOUNTS RECEIVABLE & ACCOUNTS PAYABLE - BYTD DEC 2024")
    print("=" * 70)
    print()
    
    # Load account names from cache
    ar_variations, ap_variations = get_account_variations_from_cache()
    print(f"[INFO] Loaded {len(ar_variations)} AR account variations from cache")
    print(f"[INFO] Loaded {len(ap_variations)} AP account variations from cache")
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Try to find Accounts Receivable
        print("Searching for Accounts Receivable...")
        ar_value = None
        ar_account_name = None
        
        for account_name in ar_variations:
            try:
                result = await smart_retrieve(
                    account=account_name,
                    entity="FCCS_Total Geography",
                    period="Dec",
                    years="FY24",
                    scenario="Actual"
                )
                
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rows = data.get("rows", [])
                    if rows and rows[0].get("data"):
                        value = rows[0]["data"][0]
                        if value is not None:
                            ar_value = float(value)
                            ar_account_name = account_name
                            print(f"  [FOUND] {account_name}: ${ar_value:,.2f}")
                            break
            except Exception as e:
                continue
        
        if ar_value is None:
            print("  [NOT FOUND] Could not find Accounts Receivable account")
        
        print()
        
        # Try to find Accounts Payable
        print("Searching for Accounts Payable...")
        ap_value = None
        ap_account_name = None
        
        for account_name in ap_variations:
            try:
                result = await smart_retrieve(
                    account=account_name,
                    entity="FCCS_Total Geography",
                    period="Dec",
                    years="FY24",
                    scenario="Actual"
                )
                
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rows = data.get("rows", [])
                    if rows and rows[0].get("data"):
                        value = rows[0]["data"][0]
                        if value is not None:
                            ap_value = float(value)
                            ap_account_name = account_name
                            print(f"  [FOUND] {account_name}: ${ap_value:,.2f}")
                            break
            except Exception as e:
                continue
        
        if ap_value is None:
            print("  [NOT FOUND] Could not find Accounts Payable account")
        
        print()
        print("=" * 70)
        print("RESULTS - BYTD DECEMBER 2024")
        print("=" * 70)
        print()
        
        if ar_account_name:
            print(f"Accounts Receivable ({ar_account_name}):")
            print(f"  ${ar_value:,.2f}")
        else:
            print("Accounts Receivable: NOT FOUND")
        
        print()
        
        if ap_account_name:
            print(f"Accounts Payable ({ap_account_name}):")
            print(f"  ${ap_value:,.2f}")
        else:
            print("Accounts Payable: NOT FOUND")
        
        print()
        print("=" * 70)
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(find_and_retrieve_accounts())

