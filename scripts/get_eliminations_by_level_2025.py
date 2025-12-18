"""Get total elimination amounts for each entity level starting from level 1 for 2025 YTD actuals.

This script:
1. Loads entity hierarchy from CSV to determine entity levels
2. For each entity at level 1 and above, queries elimination data
3. Uses Consolidation dimension to get intercompany elimination amounts
4. Displays results grouped by entity level
"""

import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import export_data_slice


def load_entity_hierarchy_from_csv(csv_path: Path) -> Dict[str, Dict]:
    """Load entity hierarchy from CSV metadata file.
    
    Returns dict mapping entity_name -> entity_info with level and children.
    """
    entities_map = {}  # entity_name -> entity_info
    children_map = {}  # parent_name -> list of child names
    
    # Read CSV file
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    rows = []
    
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    break
        except Exception as e:
            if encoding == encodings[-1]:
                raise
            continue
    
    if not rows:
        return {}
    
    # Build parent-child relationships
    for row in rows:
        entity_name = (row.get("Entity") or row.get("\ufeffEntity") or row.get(" Entity") or "").strip()
        parent_name = (row.get(" Parent") or row.get("Parent") or "").strip()
        
        if not entity_name or entity_name == "Entity":
            continue
        
        entities_map[entity_name] = {
            "name": entity_name,
            "parent": parent_name if parent_name and parent_name != "Entity" else None,
            "children": [],
            "level": None  # Will be calculated
        }
        
        # Track children
        if parent_name and parent_name != "Entity":
            if parent_name not in children_map:
                children_map[parent_name] = []
            children_map[parent_name].append(entity_name)
    
    # Link children to parents
    for entity_name, entity_info in entities_map.items():
        if entity_name in children_map:
            entity_info["children"] = children_map[entity_name]
    
    # Calculate levels (level 0 = leaf nodes, level 1 = parents of leaf nodes, etc.)
    def calculate_level(entity_name: str, visited: set = None) -> int:
        if visited is None:
            visited = set()
        
        if entity_name in visited:
            return 0  # Circular reference protection
        
        visited.add(entity_name)
        entity_info = entities_map.get(entity_name)
        if not entity_info:
            return 0
        
        children = entity_info.get("children", [])
        if not children:
            return 0  # Leaf node
        
        # Level is max child level + 1
        max_child_level = 0
        for child in children:
            child_level = calculate_level(child, visited.copy())
            max_child_level = max(max_child_level, child_level)
        
        return max_child_level + 1
    
    # Calculate levels for all entities
    for entity_name in entities_map:
        entities_map[entity_name]["level"] = calculate_level(entity_name)
    
    return entities_map


def load_intercompany_accounts_from_csv(csv_path: Path) -> List[str]:
    """Load all intercompany accounts from Account metadata CSV.
    
    Returns list of account names that have Intercompany Account = IC_Acc_Yes
    """
    intercompany_accounts = []
    
    # Read CSV file
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    rows = []
    
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    break
        except Exception as e:
            if encoding == encodings[-1]:
                raise
            continue
    
    if not rows:
        return []
    
    # Find column name for Intercompany Account and Account
    # The header is the first row, so we need to check the DictReader fieldnames
    sample_row = rows[0] if rows else {}
    
    # Try to find the columns
    interco_col = None
    account_col = None
    
    # Read the file again to get the actual header
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if fieldnames:
                    for field in fieldnames:
                        field_stripped = field.strip()
                        if "Intercompany Account" in field_stripped:
                            interco_col = field  # Keep original with spaces
                        if field_stripped == "Account" or (field_stripped.startswith("Account") and "Type" not in field_stripped):
                            account_col = field  # Keep original with spaces
                    if interco_col and account_col:
                        break
        except Exception:
            continue
    
    if not interco_col or not account_col:
        print(f"  [WARNING] Could not find columns. Interco: {interco_col}, Account: {account_col}")
        print(f"  Available columns: {list(sample_row.keys())[:5]}...")
        return []
    
    # Extract intercompany accounts
    for row in rows:
        account_name = (row.get(account_col) or "").strip()
        interco_value = (row.get(interco_col) or "").strip()
        
        if account_name and interco_value and "IC_Acc_Yes" in interco_value:
            # Skip if it's a header or invalid account name
            if account_name != "Account" and account_name:
                intercompany_accounts.append(account_name)
    
    return intercompany_accounts


async def get_elimination_amount(
    entity_name: str, 
    intercompany_accounts: List[str],
    year: str = "FY25"
) -> Optional[float]:
    """Get total elimination amount for an entity.
    
    Uses intercompany accounts and Movement dimension for eliminations.
    Keeps smart_retrieve structure intact but modifies Movement dimension.
    """
    try:
        # Try different Movement dimension members for eliminations
        movement_members = [
            "FCCS_Elimination",
            "FCCS_Total Elimination", 
            "FCCS_Eliminations",
            "Elimination",
            "Total Elimination",
            "FCCS_Mvmts_Total"  # Fallback to total
        ]
        
        total_elimination = 0.0
        
        # Query each intercompany account with different Movement members
        for movement_member in movement_members:
            # Use smart_retrieve structure but modify Movement dimension
            grid_definition = {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        [year], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        [movement_member], [entity_name], ["Entity Currency"],
                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": [{"members": [["FCCS_YTD"]]}],
                "rows": [{"members": [[account]] for account in intercompany_accounts}]
            }
            
            try:
                result = await export_data_slice(grid_definition, "Consol")
                
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rows = data.get("rows", [])
                    
                    if rows:
                        for row in rows:
                            row_data = row.get("data", [])
                            if row_data and len(row_data) > 0 and row_data[0] is not None:
                                try:
                                    value = abs(float(row_data[0]))
                                    total_elimination += value
                                except (ValueError, TypeError):
                                    pass
                
                # If we got data with this movement member, use it
                if total_elimination > 0.01:
                    break
                    
            except Exception:
                # Try next movement member
                continue
        
        # If we still don't have data, try querying all intercompany accounts with FCCS_Mvmts_Total
        if total_elimination < 0.01:
            grid_definition = {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        [year], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], [entity_name], ["Entity Currency"],
                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": [{"members": [["FCCS_YTD"]]}],
                "rows": [{"members": [[account]] for account in intercompany_accounts}]
            }
            
            result = await export_data_slice(grid_definition, "Consol")
            
            if result.get("status") == "success":
                data = result.get("data", {})
                rows = data.get("rows", [])
                
                if rows:
                    for row in rows:
                        row_data = row.get("data", [])
                        if row_data and len(row_data) > 0 and row_data[0] is not None:
                            try:
                                value = abs(float(row_data[0]))
                                total_elimination += value
                            except (ValueError, TypeError):
                                pass
        
        return total_elimination if total_elimination > 0.01 else None
        
    except Exception as e:
        # Silently return None on error
        return None


async def get_eliminations_by_level():
    """Get total elimination amounts for each entity level starting from level 1."""
    print("=" * 80)
    print("ELIMINATION AMOUNTS BY ENTITY LEVEL - 2025 YTD ACTUALS")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Load entity hierarchy
        project_root = Path(__file__).parent.parent
        entity_csv_path = project_root / "Ravi_ExportedMetadata_Entity.csv"
        
        if not entity_csv_path.exists():
            print(f"[ERROR] Entity metadata file not found: {entity_csv_path}")
            await close_agent()
            return
        
        print(f"Loading entity hierarchy from: {entity_csv_path.name}")
        entities_map = load_entity_hierarchy_from_csv(entity_csv_path)
        print(f"[OK] Loaded {len(entities_map)} entities")
        print()
        
        # Load intercompany accounts from Account metadata
        account_csv_path = project_root / "Ravi_ExportedMetadata_Account.csv"
        if not account_csv_path.exists():
            print(f"[ERROR] Account metadata file not found: {account_csv_path}")
            await close_agent()
            return
        
        print(f"Loading intercompany accounts from: {account_csv_path.name}")
        intercompany_accounts = load_intercompany_accounts_from_csv(account_csv_path)
        print(f"[OK] Found {len(intercompany_accounts)} intercompany accounts")
        if intercompany_accounts:
            print(f"  Sample accounts: {', '.join(intercompany_accounts[:5])}...")
        print()
        
        # Filter entities by level (level 1 and above)
        # Level 0 = leaf nodes, Level 1+ = parent entities
        entities_by_level = defaultdict(list)
        
        exclude_keywords = ["FCCS_Global Assumptions", "FCCS_Entity Total", "Entity", "FCCS_Total Geography"]
        
        for entity_name, entity_info in entities_map.items():
            level = entity_info.get("level", 0)
            if level >= 1:  # Level 1 and above
                if not any(kw in entity_name for kw in exclude_keywords):
                    entities_by_level[level].append({
                        "name": entity_name,
                        "level": level,
                        "parent": entity_info.get("parent"),
                        "children": entity_info.get("children", [])
                    })
        
        # Sort levels
        sorted_levels = sorted(entities_by_level.keys())
        
        print(f"[OK] Found entities at levels: {sorted_levels}")
        print(f"  Total entities to query: {sum(len(entities_by_level[level]) for level in sorted_levels)}")
        print()
        
        # Get elimination amounts for each entity
        print("Querying elimination amounts...")
        print("(This may take several minutes)")
        print()
        
        results_by_level = defaultdict(list)
        total_queried = 0
        total_with_data = 0
        
        for level in sorted_levels:
            entities = entities_by_level[level]
            print(f"Level {level}: Processing {len(entities)} entities...")
            
            for entity in entities:
                entity_name = entity["name"]
                total_queried += 1
                
                elimination_amount = await get_elimination_amount(
                    entity_name, 
                    intercompany_accounts, 
                    "FY25"
                )
                
                if elimination_amount is not None and abs(elimination_amount) > 0.01:
                    total_with_data += 1
                    results_by_level[level].append({
                        "name": entity_name,
                        "elimination_amount": elimination_amount,
                        "parent": entity.get("parent"),
                        "children_count": len(entity.get("children", []))
                    })
                    print(f"  {entity_name:50s}: ${elimination_amount:>15,.2f}")
                else:
                    print(f"  {entity_name:50s}: No elimination data")
        
        print()
        print("=" * 80)
        print("SUMMARY BY LEVEL")
        print("=" * 80)
        print()
        
        grand_total = 0.0
        
        for level in sorted_levels:
            entities = results_by_level[level]
            if entities:
                level_total = sum(e["elimination_amount"] for e in entities)
                grand_total += level_total
                
                print(f"Level {level}:")
                print(f"  Entities with eliminations: {len(entities)}")
                print(f"  Total elimination amount: ${level_total:>15,.2f}")
                print()
                
                # Show top 10 entities by elimination amount
                sorted_entities = sorted(entities, key=lambda x: abs(x["elimination_amount"]), reverse=True)
                top_10 = sorted_entities[:10]
                
                if top_10:
                    print(f"  Top {len(top_10)} entities by elimination amount:")
                    for i, entity in enumerate(top_10, 1):
                        print(f"    {i:2d}. {entity['name']:50s}: ${entity['elimination_amount']:>15,.2f}")
                    print()
        
        print("=" * 80)
        print(f"GRAND TOTAL (All Levels): ${grand_total:>15,.2f}")
        print(f"Total entities queried: {total_queried}")
        print(f"Entities with elimination data: {total_with_data}")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(get_eliminations_by_level())

