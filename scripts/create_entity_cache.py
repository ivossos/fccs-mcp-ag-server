"""Helper script to create Entity dimension cache file."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.utils.cache import MEMBERS_CACHE_DIR, get_cache_file_path


def create_entity_cache():
    """Create or update Entity cache file."""
    print("=" * 70)
    print("Create Entity Dimension Cache File")
    print("=" * 70)
    print()
    
    cache_file = get_cache_file_path("Consol", "Entity")
    
    print(f"Cache file location: {cache_file}")
    print()
    
    if cache_file.exists():
        print("[INFO] Cache file already exists")
        print()
        print("Current contents:")
        print("-" * 70)
        with open(cache_file, "r", encoding="utf-8") as f:
            current = json.load(f)
            items = current.get("items", [])
            print(f"  Entities: {len(items)}")
            for item in items[:10]:
                print(f"    - {item.get('name', 'Unknown')}")
            if len(items) > 10:
                print(f"    ... and {len(items) - 10} more")
        print()
        
        response = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return
    
    print("Enter entity names (one per line, or comma-separated).")
    print("Press Enter twice or type 'done' to finish:")
    print()
    
    entities = []
    print("Entity names:")
    
    # Try to read from command line args first
    if len(sys.argv) > 1:
        # Comma-separated list
        entity_names = sys.argv[1].split(",")
        entities = [{"name": name.strip(), "description": name.strip(), "parent": "Root"} 
                   for name in entity_names if name.strip()]
        print(f"  Using {len(entities)} entities from command line")
    else:
        # Interactive input
        while True:
            line = input("  > ").strip()
            if not line or line.lower() == 'done':
                break
            
            # Handle comma-separated
            if ',' in line:
                names = [n.strip() for n in line.split(',')]
                entities.extend([{"name": name, "description": name, "parent": "Root"} 
                               for name in names if name])
            else:
                entities.append({
                    "name": line,
                    "description": line,
                    "parent": "Root"
                })
    
    if not entities:
        print("\nNo entities provided. Creating template file...")
        entities = [
            {
                "name": "FCCS_Total Geography",
                "description": "Total Geography",
                "parent": "Root"
            },
            {
                "name": "FCCS_Entity Total",
                "description": "Entity Total",
                "parent": "Root"
            }
        ]
        print("Template created with example entities.")
        print("Edit the file manually to add your actual entity names.")
    
    # Create cache data structure
    cache_data = {
        "items": entities,
        "metadata": {
            "app_name": "Consol",
            "dimension_name": "Entity",
            "total_members": len(entities),
            "created_by": "create_entity_cache.py"
        }
    }
    
    # Write to file
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 70)
        print(f"[SUCCESS] Cache file created with {len(entities)} entities")
        print(f"Location: {cache_file}")
        print()
        print("Entity names saved:")
        for i, entity in enumerate(entities[:20], 1):
            print(f"  {i}. {entity['name']}")
        if len(entities) > 20:
            print(f"  ... and {len(entities) - 20} more")
        print()
        print("You can now:")
        print("  1. Run: python scripts/get_top_10_performers.py")
        print("  2. Or edit the file manually to add more entities")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create cache file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_entity_cache()












