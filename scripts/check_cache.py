"""Check what's in the local cache for dimension members."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.utils.cache import list_cached_dimensions, load_members_from_cache
import json


def check_cache():
    """Check cached dimension members."""
    print("=" * 60)
    print("Dimension Members Cache Check")
    print("=" * 60)
    print()
    
    cached = list_cached_dimensions()
    
    if not cached:
        print("No cached dimensions found.")
        print()
        print("To populate cache:")
        print("  1. Run: python scripts/populate_cache.py")
        print("  2. Or manually create cache files in .cache/members/")
        print("     Format: {app_name}_{dimension_name}.json")
        return
    
    print(f"Found {len(cached)} cached dimension(s):")
    print()
    
    for item in cached:
        app_name = item['app_name']
        dim_name = item['dimension_name']
        cache_file = item['cache_file']
        
        print(f"  {app_name} / {dim_name}")
        print(f"    Cache file: {cache_file}")
        
        # Load and show member count
        members = load_members_from_cache(app_name, dim_name)
        if members:
            items = members.get("items", [])
            print(f"    Members: {len(items)}")
            
            # Show first few members
            if items:
                print(f"    Sample members:")
                for member in items[:5]:
                    name = member.get("name", "Unknown")
                    print(f"      - {name}")
                if len(items) > 5:
                    print(f"      ... and {len(items) - 5} more")
        print()


if __name__ == "__main__":
    check_cache()


