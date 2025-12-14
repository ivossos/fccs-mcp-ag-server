"""Script to populate local cache with dimension members."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.dimensions import get_dimensions, get_members
from fccs_agent.utils.cache import list_cached_dimensions


async def populate_cache():
    """Populate cache with dimension members."""
    print("=" * 60)
    print("Populating Dimension Members Cache")
    print("=" * 60)
    print()
    
    try:
        # Initialize agent
        config = load_config()
        await initialize_agent(config)
        print("[OK] Agent initialized")
        print()
        
        # Get all dimensions
        print("Getting list of dimensions...")
        dims_result = await get_dimensions()
        if dims_result.get("status") != "success":
            print(f"Error: {dims_result.get('error', 'Unknown error')}")
            return
        
        dimensions = dims_result.get("data", {}).get("items", [])
        print(f"[OK] Found {len(dimensions)} dimensions")
        print()
        
        # Try to cache members for each dimension
        cached_count = 0
        failed_count = 0
        
        for dim in dimensions:
            dim_name = dim.get("name")
            if not dim_name:
                continue
            
            print(f"Caching members for: {dim_name}...", end=" ")
            try:
                members_result = await get_members(dim_name)
                if members_result.get("status") == "success":
                    print("[OK]")
                    cached_count += 1
                else:
                    print(f"[FAILED] {members_result.get('error', 'Unknown error')}")
                    failed_count += 1
            except Exception as e:
                print(f"[FAILED] {e}")
                failed_count += 1
        
        print()
        print("=" * 60)
        print(f"Cache population complete:")
        print(f"  - Successfully cached: {cached_count} dimensions")
        print(f"  - Failed: {failed_count} dimensions")
        print("=" * 60)
        
        # Show cached dimensions
        print()
        print("Cached dimensions:")
        cached = list_cached_dimensions()
        for item in cached:
            print(f"  - {item['app_name']} / {item['dimension_name']}")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(populate_cache())

