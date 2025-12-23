"""Load account cache from the exported CSV file in project root."""

import csv
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.utils.cache import get_cache_file_path, MEMBERS_CACHE_DIR


def load_accounts_from_csv():
    """Load accounts from Ravi_ExportedMetadata_Account.csv and create cache file."""
    print("=" * 70)
    print("Loading Account Cache from CSV File")
    print("=" * 70)
    print()
    
    csv_file = Path(__file__).parent.parent / "Ravi_ExportedMetadata_Account.csv"
    
    if not csv_file.exists():
        print(f"[ERROR] CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"Reading: {csv_file}")
    print()
    
    accounts = []
    
    try:
        # Try different encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with open(csv_file, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        account_name = row.get("Account", "").strip()
                        parent = row.get("Parent", "").strip()
                        alias = row.get("Alias: Default", "").strip()
                        description = row.get("Description", "").strip()
                        
                        if account_name and account_name != "Account":  # Skip header
                            accounts.append({
                                "name": account_name,
                                "parent": parent if parent else "Root",
                                "description": description or alias or account_name,
                                "alias": alias if alias else None
                            })
                    
                    if accounts:
                        print(f"  Used encoding: {encoding}")
                        break
            except Exception as e:
                if encoding == encodings[-1]:
                    raise
                continue
        
        print(f"[OK] Loaded {len(accounts)} accounts from CSV")
        print()
        
        # Create cache file
        cache_file = get_cache_file_path("Consol", "Account")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        cache_data = {
            "items": accounts,
            "metadata": {
                "app_name": "Consol",
                "dimension_name": "Account",
                "total_members": len(accounts),
                "source": "Ravi_ExportedMetadata_Account.csv",
                "created_by": "load_account_cache_from_csv.py"
            }
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Cache file created: {cache_file}")
        print(f"  Accounts cached: {len(accounts)}")
        print()
        
        # Show sample accounts, especially looking for AR/AP related
        print("Sample accounts:")
        ar_ap_accounts = []
        for account in accounts:
            name = account['name'].lower()
            if any(term in name for term in ['receivable', 'payable', 'ar', 'ap', 'acct']):
                ar_ap_accounts.append(account)
        
        if ar_ap_accounts:
            print("\nAccounts Receivable/Payable related accounts:")
            for account in ar_ap_accounts[:20]:
                print(f"  - {account['name']} (Parent: {account['parent']})")
            if len(ar_ap_accounts) > 20:
                print(f"  ... and {len(ar_ap_accounts) - 20} more AR/AP related")
        
        print("\nOther sample accounts:")
        for i, account in enumerate(accounts[:10], 1):
            if account not in ar_ap_accounts:
                print(f"  {i}. {account['name']} (Parent: {account['parent']})")
        if len(accounts) > 10:
            print(f"  ... and {len(accounts) - 10} more total accounts")
        
        print()
        print("=" * 70)
        print("Cache populated successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Failed to process CSV: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    load_accounts_from_csv()















