"""Check unbalanced entities for 2024 - from bottom level to top level.

An entity is considered unbalanced if:
Total Assets ≠ Total Liabilities and Equity
"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


# Tolerance for balance check (entities within this amount are considered balanced)
BALANCE_TOLERANCE = 0.01


def load_entity_hierarchy_from_csv(csv_path: Path) -> List[Dict]:
    """Load entity hierarchy from CSV metadata file.
    
    Returns list of entities with their hierarchy information.
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
        print(f"DEBUG: No rows read from CSV", file=sys.stderr)
        return []
    
    # Build parent-child relationships
    for row in rows:
        # Handle column names with BOM, leading spaces - try all variations
        # BOM character \ufeff might be present in first column when using utf-8-sig
        entity_name = (row.get("Entity") or row.get("\ufeffEntity") or row.get(" Entity") or "").strip()
        parent_name = (row.get(" Parent") or row.get("Parent") or "").strip()
        
        if not entity_name or entity_name == "Entity":  # Skip header or empty
            continue
        # Initialize entity info
        entities_map[entity_name] = {
            "name": entity_name,
            "parent": parent_name if parent_name and parent_name != "Entity" else None,
            "children": []
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
    
    if not entities_map:
        return []
    
    # Calculate levels (bottom level = 0 for leaf nodes, increasing upward)
    def calculate_level(entity_name: str, visited: set = None) -> int:
        """Calculate level of entity (0 = bottom/leaf, increasing upward)."""
        if visited is None:
            visited = set()
        
        if entity_name in visited:
            # Circular reference, return 0
            return 0
        
        visited.add(entity_name)
        
        entity_info = entities_map.get(entity_name)
        if not entity_info:
            return 0
        
        children = entity_info.get("children", [])
        
        # If no children, this is a leaf node (bottom level = 0)
        if not children:
            return 0
        
        # Level is max of children's levels + 1
        # Use a new visited set for each child to allow proper traversal
        child_levels = []
        for child in children:
            child_level = calculate_level(child, set(visited))  # Create new set for each child
            child_levels.append(child_level)
        
        return max(child_levels) + 1 if child_levels else 0
    
    # Calculate levels for all entities
    entities_list = []
    for entity_name, entity_info in entities_map.items():
        level = calculate_level(entity_name)
        is_leaf = len(entity_info.get("children", [])) == 0
        
        entities_list.append({
            "name": entity_name,
            "level": level,
            "parent": entity_info["parent"],
            "is_leaf": is_leaf,
            "children_count": len(entity_info.get("children", []))
        })
    
    return entities_list


def generate_report(
    unbalanced_entities: List[Dict],
    total_checked: int,
    no_data: int,
    level_counts: Dict[int, int],
    largest_imbalances: List[Dict]
) -> str:
    """Generate HTML report file with unbalanced entities."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"Unbalanced_Entities_Report_2024_{timestamp}.html"
    project_root = Path(__file__).parent.parent
    
    # Sort entities by level for display
    unbalanced_entities_sorted = sorted(unbalanced_entities, key=lambda x: (x["level"], -abs(x["difference"])))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unbalanced Entities Report - 2024</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f4788;
            border-bottom: 3px solid #1f4788;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #3d6bb3;
            margin-top: 20px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #1f4788;
        }}
        .summary-item strong {{
            display: block;
            color: #1f4788;
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background-color: #1f4788;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .level-header {{
            background-color: #2c5aa0;
            color: white;
            font-weight: bold;
            padding: 8px 12px;
            margin-top: 20px;
        }}
        .negative {{
            color: #d32f2f;
        }}
        .positive {{
            color: #388e3c;
        }}
        .leaf-indicator {{
            color: #666;
            font-size: 11px;
            font-style: italic;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Unbalanced Entities Report - 2024</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        <p><strong>Report Period:</strong> FY24 (December YTD)</p>
        <p><strong>Balance Check:</strong> Total Assets vs Total Liabilities and Equity</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <strong>Total Entities Checked</strong>
                    <span>{total_checked}</span>
                </div>
                <div class="summary-item">
                    <strong>Entities with Data</strong>
                    <span>{total_checked - no_data}</span>
                </div>
                <div class="summary-item">
                    <strong>Unbalanced Entities</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(unbalanced_entities)}</span>
                </div>
                <div class="summary-item">
                    <strong>Balanced Entities</strong>
                    <span style="color: #388e3c; font-weight: bold;">{total_checked - no_data - len(unbalanced_entities)}</span>
                </div>
            </div>
        </div>
        
        <h2>Unbalanced Entities by Hierarchy Level</h2>
        <p>Entities are shown from bottom level (leaf nodes) to top level (consolidated entities).</p>
"""
    
    # Group by level
    current_level = None
    for entity in unbalanced_entities_sorted:
        if current_level != entity["level"]:
            if current_level is not None:
                html_content += "</table>\n"
            current_level = entity["level"]
            level_label = "BOTTOM LEVEL (Leaf Nodes)" if entity["level"] == 0 else f"LEVEL {entity['level']}"
            html_content += f"""
        <h3 class="level-header">{level_label}</h3>
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th style="text-align: right;">Total Assets</th>
                    <th style="text-align: right;">Liab + Equity</th>
                    <th style="text-align: right;">Difference</th>
                    <th>Parent</th>
                </tr>
            </thead>
            <tbody>
"""
        
        diff_class = "negative" if entity["difference"] < 0 else "positive"
        leaf_indicator = " <span class='leaf-indicator'>(Leaf)</span>" if entity["is_leaf"] else ""
        parent_name = entity.get("parent", "N/A") or "N/A"
        
        html_content += f"""
                <tr>
                    <td>{entity['name']}{leaf_indicator}</td>
                    <td style="text-align: right;">${entity['assets']:,.2f}</td>
                    <td style="text-align: right;">${entity['liabilities_equity']:,.2f}</td>
                    <td style="text-align: right;" class="{diff_class}"><strong>${entity['difference']:,.2f}</strong></td>
                    <td>{parent_name}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Statistics by Level</h2>
        <table>
            <thead>
                <tr>
                    <th>Level</th>
                    <th style="text-align: right;">Count</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for level in sorted(level_counts.keys()):
        count = level_counts[level]
        level_label = "BOTTOM" if level == 0 else f"LEVEL {level}"
        html_content += f"""
                <tr>
                    <td>{level_label}</td>
                    <td style="text-align: right;"><strong>{count}</strong></td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Top 10 Largest Imbalances</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity Name</th>
                    <th style="text-align: right;">Absolute Difference</th>
                    <th>Level</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for i, entity in enumerate(largest_imbalances, 1):
        diff_class = "negative" if entity["difference"] < 0 else "positive"
        html_content += f"""
                <tr>
                    <td><strong>{i}</strong></td>
                    <td>{entity['name']}</td>
                    <td style="text-align: right;" class="{diff_class}"><strong>${abs(entity['difference']):,.2f}</strong></td>
                    <td>{entity['level']}</td>
                </tr>
"""
    
    html_content += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>FCCS Unbalanced Entities Report</strong></p>
            <p>Data from Oracle EPM Cloud Financial Consolidation and Close (FCCS)</p>
            <p>Application: Consol | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    report_path = project_root / report_filename
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(report_path)


async def get_balance_sheet_values(entity_name: str, year: str = "FY24") -> Optional[Tuple[float, float, float]]:
    """Get balance sheet values for an entity.
    
    Returns: (Total Assets, Total Liabilities and Equity, Difference) or None if error.
    """
    try:
        # Get Total Assets
        assets_result = await smart_retrieve(
            account="FCCS_Total Assets",
            entity=entity_name,
            period="Dec",
            years=year,
            scenario="Actual"
        )
        
        # Get Total Liabilities and Equity
        liabilities_result = await smart_retrieve(
            account="FCCS_Total Liabilities and Equity",
            entity=entity_name,
            period="Dec",
            years=year,
            scenario="Actual"
        )
        
        assets_value = None
        liabilities_value = None
        
        if assets_result.get("status") == "success":
            data = assets_result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                if value is not None:
                    assets_value = float(value)
        
        if liabilities_result.get("status") == "success":
            data = liabilities_result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                if value is not None:
                    liabilities_value = float(value)
        
        # If both values are None, entity might not have data
        if assets_value is None and liabilities_value is None:
            return None
        
        # If one is None, treat as 0 for calculation
        assets_value = assets_value if assets_value is not None else 0.0
        liabilities_value = liabilities_value if liabilities_value is not None else 0.0
        
        difference = assets_value - liabilities_value
        
        return (assets_value, liabilities_value, difference)
        
    except Exception as e:
        # Silently handle errors - entity might not exist or have data
        return None


async def check_unbalanced_entities_2024():
    """Check unbalanced entities for 2024, from bottom to top level."""
    print("=" * 80)
    print("UNBALANCED ENTITIES CHECK - 2024")
    print("Checking from bottom level to top level")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Load entity hierarchy from CSV metadata file
        project_root = Path(__file__).parent.parent
        entity_csv_path = project_root / "Ravi_ExportedMetadata_Entity.csv"
        
        if not entity_csv_path.exists():
            print(f"[ERROR] Entity metadata file not found: {entity_csv_path}")
            print(f"Current working directory: {Path.cwd()}")
            await close_agent()
            return
        
        print(f"Loading entity hierarchy from: {entity_csv_path.name}")
        all_entities = load_entity_hierarchy_from_csv(entity_csv_path)
        
        if not all_entities:
            print("[ERROR] No entities loaded from CSV file")
            print(f"CSV file exists: {entity_csv_path.exists()}")
            print(f"CSV file size: {entity_csv_path.stat().st_size if entity_csv_path.exists() else 0} bytes")
            await close_agent()
            return
        print(f"[OK] Loaded {len(all_entities)} entities from CSV")
        print()
        
        # Filter out system entities
        exclude_keywords = ["FCCS_Global Assumptions", "FCCS_Entity Total", "Entity"]
        filtered_entities = [
            e for e in all_entities 
            if not any(kw in e["name"] for kw in exclude_keywords)
        ]
        
        # Sort by level (bottom level first, then going up)
        # Within same level, sort by name for consistency
        filtered_entities.sort(key=lambda x: (x["level"], x["name"]))
        
        if filtered_entities:
            print(f"[OK] Found {len(filtered_entities)} entities to check")
            print(f"Levels range from {min(e['level'] for e in filtered_entities)} (bottom) to {max(e['level'] for e in filtered_entities)} (top)")
        else:
            print("[WARNING] No entities found after filtering")
            await close_agent()
            return
        print()
        
        # Check balance for each entity
        print("Checking balance for each entity (Assets vs Liabilities + Equity)...")
        print("(This may take several minutes)")
        print()
        
        unbalanced_entities = []
        checked = 0
        no_data = 0
        
        for entity_info in filtered_entities:
            checked += 1
            entity_name = entity_info["name"]
            
            if checked % 20 == 0:
                print(f"  Progress: {checked}/{len(filtered_entities)} (Found {len(unbalanced_entities)} unbalanced, {no_data} no data)...")
            
            balance_values = await get_balance_sheet_values(entity_name, "FY24")
            
            if balance_values is None:
                no_data += 1
                continue
            
            assets, liabilities, difference = balance_values
            
            # Check if unbalanced (difference outside tolerance)
            if abs(difference) > BALANCE_TOLERANCE:
                unbalanced_entities.append({
                    "name": entity_name,
                    "level": entity_info["level"],
                    "parent": entity_info["parent"],
                    "is_leaf": entity_info["is_leaf"],
                    "assets": assets,
                    "liabilities_equity": liabilities,
                    "difference": difference
                })
        
        print()
        print("=" * 80)
        print("RESULTS - UNBALANCED ENTITIES FOR 2024")
        print("=" * 80)
        print()
        
        # Initialize variables that may be used in report generation
        level_counts = {}
        largest_imbalances = []
        
        if not unbalanced_entities:
            print("✓ No unbalanced entities found!")
            print(f"All {checked - no_data} entities with data are balanced.")
        else:
            # Sort by level (bottom to top), then by absolute difference (largest first)
            unbalanced_entities.sort(key=lambda x: (x["level"], -abs(x["difference"])))
            
            print(f"Found {len(unbalanced_entities)} unbalanced entities:")
            print()
            print(f"{'Level':<6} {'Entity':<50} {'Assets':>20} {'Liab+Equity':>20} {'Difference':>20}")
            print("-" * 120)
            
            # Group by level for better readability
            current_level = None
            for entity in unbalanced_entities:
                if current_level != entity["level"]:
                    if current_level is not None:
                        print()
                    level_label = "BOTTOM" if entity["level"] == 0 else f"LEVEL {entity['level']}"
                    print(f"\n{level_label} (Level {entity['level']}):")
                    print("-" * 120)
                    current_level = entity["level"]
                
                entity_name = entity["name"][:48]  # Truncate if too long
                leaf_indicator = " [LEAF]" if entity["is_leaf"] else ""
                print(f"{entity['level']:<6} {entity_name:<50}{leaf_indicator} ${entity['assets']:>19,.2f} ${entity['liabilities_equity']:>19,.2f} ${entity['difference']:>19,.2f}")
            
            print()
            print("=" * 120)
            print("SUMMARY")
            print("=" * 120)
            print(f"Total entities checked: {checked}")
            print(f"Entities with data: {checked - no_data}")
            print(f"Unbalanced entities: {len(unbalanced_entities)}")
            print(f"Balanced entities: {checked - no_data - len(unbalanced_entities)}")
            print()
            
            # Statistics by level
            print("Unbalanced entities by level:")
            for entity in unbalanced_entities:
                level = entity["level"]
                level_counts[level] = level_counts.get(level, 0) + 1
            
            for level in sorted(level_counts.keys()):
                count = level_counts[level]
                level_label = "BOTTOM" if level == 0 else f"LEVEL {level}"
                print(f"  {level_label}: {count} entities")
            
            print()
            # Largest imbalances
            largest_imbalances = sorted(unbalanced_entities, key=lambda x: abs(x["difference"]), reverse=True)[:10]
            print("Top 10 largest imbalances:")
            for i, entity in enumerate(largest_imbalances, 1):
                print(f"  {i}. {entity['name']}: ${abs(entity['difference']):,.2f}")
        
        # Generate report (only if there are unbalanced entities)
        if unbalanced_entities:
            print()
            print("=" * 80)
            print("GENERATING REPORT")
            print("=" * 80)
            report_filename = generate_report(unbalanced_entities, checked, no_data, level_counts, largest_imbalances)
            print(f"[OK] Report generated: {report_filename}")
            print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(check_unbalanced_entities_2024())

