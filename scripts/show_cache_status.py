"""Show detailed cache status."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.utils.cache import CACHE_DIR, MEMBERS_CACHE_DIR, list_cached_dimensions, load_members_from_cache


def show_cache_status():
    """Show detailed cache status."""
    print("=" * 70)
    print("LOCAL CACHE STATUS")
    print("=" * 70)
    print()
    
    # Check cache directory
    print(f"Cache Directory: {CACHE_DIR}")
    print(f"  Exists: {CACHE_DIR.exists()}")
    print()
    
    print(f"Members Cache Directory: {MEMBERS_CACHE_DIR}")
    print(f"  Exists: {MEMBERS_CACHE_DIR.exists()}")
    
    if MEMBERS_CACHE_DIR.exists():
        cache_files = list(MEMBERS_CACHE_DIR.glob("*.json"))
        print(f"  Files: {len(cache_files)}")
        
        if cache_files:
            print()
            print("Cached Dimension Members:")
            print("-" * 70)
            for cache_file in sorted(cache_files):
                size = cache_file.stat().st_size
                mtime = cache_file.stat().st_mtime
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {cache_file.name}")
                print(f"    Size: {size:,} bytes")
                print(f"    Modified: {mtime_str}")
                
                # Try to load and show info
                name_parts = cache_file.stem.split("_", 1)
                if len(name_parts) == 2:
                    app_name, dim_name = name_parts
                    members = load_members_from_cache(app_name, dim_name)
                    if members:
                        items = members.get("items", [])
                        print(f"    Members: {len(items)}")
                        if items:
                            print(f"    Sample: {', '.join([item.get('name', '?')[:20] for item in items[:5]])}")
                print()
        else:
            print("  No cache files found")
    else:
        print("  Directory does not exist")
    
    print()
    print("=" * 70)
    print("Cache Usage:")
    print("  - Cache files are stored in: .cache/members/")
    print("  - Format: {app_name}_{dimension_name}.json")
    print("  - The system checks cache FIRST before making API calls")
    print()
    print("To populate cache:")
    print("  1. Run: python scripts/populate_cache.py")
    print("  2. Or manually create JSON files in .cache/members/")
    print("=" * 70)


if __name__ == "__main__":
    show_cache_status()

