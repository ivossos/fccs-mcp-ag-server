"""Create Account dimension cache by fetching from FCCS."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.dimensions import get_members
from fccs_agent.utils.cache import load_members_from_cache, save_members_to_cache


async def create_account_cache():
    """Fetch and cache Account dimension members."""
    print("=" * 70)
    print("CREATING ACCOUNT DIMENSION CACHE")
    print("=" * 70)
    print()
    
    try:
        # First check if cache already exists
        cached = load_members_from_cache("Consol", "Account")
        if cached:
            items = cached.get("items", [])
            print(f"[INFO] Account cache already exists with {len(items)} members")
            print(f"Cache file: .cache/members/Consol_Account.json")
            print()
            print("Sample accounts:")
            for item in items[:10]:
                print(f"  - {item.get('name', 'Unknown')}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
            return
        
        # Initialize agent and fetch
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        print("Fetching Account dimension members...")
        result = await get_members("Account")
        
        if result.get("status") == "success":
            members = result.get("data", {})
            items = members.get("items", [])
            print(f"[OK] Retrieved {len(items)} Account members")
            print()
            
            # Save to cache
            save_members_to_cache("Consol", "Account", members)
            print(f"[OK] Saved to cache: .cache/members/Consol_Account.json")
            print()
            
            # Show sample accounts
            print("Sample accounts:")
            for item in items[:20]:
                name = item.get("name", "Unknown")
                desc = item.get("description", "")
                print(f"  - {name}" + (f" ({desc})" if desc else ""))
            if len(items) > 20:
                print(f"  ... and {len(items) - 20} more")
        else:
            error = result.get("error", "Unknown error")
            print(f"[ERROR] Could not fetch Account members: {error}")
            print()
            print("Note: Account dimension API may not be available.")
            print("You may need to:")
            print("  1. Export Account list from Oracle Smart View")
            print("  2. Convert to JSON format")
            print("  3. Save to .cache/members/Consol_Account.json")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_account_cache())


