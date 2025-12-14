"""Load entity cache from the exported CSV file in project root."""

import csv
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.utils.cache import get_cache_file_path, MEMBERS_CACHE_DIR


def load_entities_from_csv():
    """Load entities from Ravi_ExportedMetadata_Entity.csv and create cache file."""
    print("=" * 70)
    print("Loading Entity Cache from CSV File")
    print("=" * 70)
    print()
    
    csv_file = Path(__file__).parent.parent / "Ravi_ExportedMetadata_Entity.csv"
    
    if not csv_file.exists():
        print(f"[ERROR] CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"Reading: {csv_file}")
    print()
    
    entities = []
    
    try:
        # Try different encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with open(csv_file, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        entity_name = row.get("Entity", "").strip()
                        parent = row.get("Parent", "").strip()
                        alias = row.get("Alias: Default", "").strip()
                        description = row.get("Description", "").strip()
                        
                        if entity_name and entity_name != "Entity":  # Skip header
                            entities.append({
                                "name": entity_name,
                                "parent": parent if parent else "Root",
                                "description": description or alias or entity_name,
                                "alias": alias if alias else None
                            })
                    
                    if entities:
                        print(f"  Used encoding: {encoding}")
                        break
            except Exception as e:
                if encoding == encodings[-1]:
                    raise
                continue
        
        print(f"[OK] Loaded {len(entities)} entities from CSV")
        print()
        
        # Create cache file
        cache_file = get_cache_file_path("Consol", "Entity")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        cache_data = {
            "items": entities,
            "metadata": {
                "app_name": "Consol",
                "dimension_name": "Entity",
                "total_members": len(entities),
                "source": "Ravi_ExportedMetadata_Entity.csv",
                "created_by": "load_entity_cache_from_csv.py"
            }
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Cache file created: {cache_file}")
        print(f"  Entities cached: {len(entities)}")
        print()
        
        # Show sample entities
        print("Sample entities:")
        for i, entity in enumerate(entities[:20], 1):
            print(f"  {i}. {entity['name']} (Parent: {entity['parent']})")
        if len(entities) > 20:
            print(f"  ... and {len(entities) - 20} more")
        
        print()
        print("=" * 70)
        print("Cache populated successfully!")
        print("You can now run: python scripts/get_top_10_performers.py")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Failed to process CSV: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    load_entities_from_csv()

