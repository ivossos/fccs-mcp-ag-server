"""Comprehensive data quality check for FY24 Dec.

Checks:
1. Entities with zero revenue
2. Accounts with null values
3. Unbalanced entities (Assets != Liabilities + Equity)
"""

import asyncio
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache


# Tolerance for balance check
BALANCE_TOLERANCE = 0.01

# Key accounts to check for null values
KEY_ACCOUNTS = [
    "FCCS_Sales",
    "FCCS_Net Income",
    "FCCS_Total Assets",
    "FCCS_Total Liabilities and Equity",
    "FCCS_Operating Income",
    "FCCS_Total Pre Tax Income"
]

# Revenue account for zero revenue check
REVENUE_ACCOUNT = "FCCS_Sales"


def load_entity_hierarchy_from_cache() -> List[Dict]:
    """Load entity hierarchy from cache (JSON or CSV).
    
    Returns list of entities with their hierarchy information.
    """
    # First try JSON cache
    cache_data = load_members_from_cache("Consol", "Entity")
    
    if not cache_data:
        print("[WARNING] No entity cache found. Please ensure cache files exist.")
        return []
    
    items = cache_data.get("items", [])
    if not items:
        return []
    
    # Build parent-child relationships
    entities_map = {}
    children_map = {}
    
    for item in items:
        entity_name = item.get("name") or item.get("memberName")
        parent_name = item.get("parent") or item.get("parentName")
        
        if not entity_name:
            continue
        
        entities_map[entity_name] = {
            "name": entity_name,
            "parent": parent_name if parent_name and parent_name != "Root" else None,
            "children": []
        }
        
        if parent_name and parent_name != "Root":
            if parent_name not in children_map:
                children_map[parent_name] = []
            children_map[parent_name].append(entity_name)
    
    # Link children to parents
    for entity_name, entity_info in entities_map.items():
        if entity_name in children_map:
            entity_info["children"] = children_map[entity_name]
    
    # Calculate levels (bottom level = 0 for leaf nodes, increasing upward)
    def calculate_level(entity_name: str, visited: set = None) -> int:
        """Calculate level of entity (0 = bottom/leaf, increasing upward)."""
        if visited is None:
            visited = set()
        
        if entity_name in visited:
            return 0
        
        visited.add(entity_name)
        
        entity_info = entities_map.get(entity_name)
        if not entity_info:
            return 0
        
        children = entity_info.get("children", [])
        
        if not children:
            return 0
        
        child_levels = []
        for child in children:
            child_level = calculate_level(child, set(visited))
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


async def get_revenue_value(entity_name: str) -> Optional[float]:
    """Get revenue value for an entity for FY24 Dec."""
    try:
        result = await smart_retrieve(
            account=REVENUE_ACCOUNT,
            entity=entity_name,
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
                    return float(value)
        return None
    except Exception as e:
        print(f"  [ERROR] Error getting revenue for {entity_name}: {e}")
        return None


async def get_account_value(account_name: str, entity_name: str) -> Optional[float]:
    """Get account value for an entity for FY24 Dec."""
    try:
        result = await smart_retrieve(
            account=account_name,
            entity=entity_name,
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
                    return float(value)
        return None
    except Exception as e:
        return None


async def get_balance_sheet_values(entity_name: str) -> Optional[Tuple[float, float, float]]:
    """Get balance sheet values for an entity.
    
    Returns: (Total Assets, Total Liabilities and Equity, Difference) or None if error.
    """
    try:
        # Get Total Assets
        assets_result = await smart_retrieve(
            account="FCCS_Total Assets",
            entity=entity_name,
            period="Dec",
            years="FY24",
            scenario="Actual"
        )
        
        # Get Total Liabilities and Equity
        liabilities_result = await smart_retrieve(
            account="FCCS_Total Liabilities and Equity",
            entity=entity_name,
            period="Dec",
            years="FY24",
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
        return None


def generate_report(
    zero_revenue_entities: List[Dict],
    null_account_entities: List[Dict],
    unbalanced_entities: List[Dict],
    total_entities_checked: int,
    entities_with_data: int
) -> str:
    """Generate HTML report file with data quality issues."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"Data_Quality_Check_FY24_Dec_{timestamp}.html"
    project_root = Path(__file__).parent.parent
    report_path = project_root / report_filename
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality Check - FY24 Dec</title>
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
        .summary-item.warning {{
            border-left-color: #ff9800;
        }}
        .summary-item.error {{
            border-left-color: #d32f2f;
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
        .negative {{
            color: #d32f2f;
        }}
        .positive {{
            color: #388e3c;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .no-issues {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            color: #2e7d32;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Data Quality Check Report - FY24 Dec</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        <p><strong>Report Period:</strong> FY24 (December YTD)</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <strong>Total Entities Checked</strong>
                    <span>{total_entities_checked}</span>
                </div>
                <div class="summary-item">
                    <strong>Entities with Data</strong>
                    <span>{entities_with_data}</span>
                </div>
                <div class="summary-item error">
                    <strong>Entities with Zero Revenue</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(zero_revenue_entities)}</span>
                </div>
                <div class="summary-item error">
                    <strong>Entities with Null Account Values</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(null_account_entities)}</span>
                </div>
                <div class="summary-item error">
                    <strong>Unbalanced Entities</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(unbalanced_entities)}</span>
                </div>
            </div>
        </div>
        
        <h2>1. Entities with Zero Revenue</h2>
"""
    
    if zero_revenue_entities:
        html_content += f"""
        <p>Found <strong>{len(zero_revenue_entities)}</strong> entities with zero revenue (FCCS_Sales = 0 or null).</p>
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th>Parent</th>
                    <th>Level</th>
                    <th>Revenue (FCCS_Sales)</th>
                    <th>Is Leaf</th>
                </tr>
            </thead>
            <tbody>
"""
        for entity in sorted(zero_revenue_entities, key=lambda x: (x["level"], x["name"])):
            html_content += f"""
                <tr>
                    <td>{entity['name']}</td>
                    <td>{entity.get('parent', 'N/A')}</td>
                    <td>{entity['level']}</td>
                    <td class="negative">${entity.get('revenue', 0):,.2f}</td>
                    <td>{'Yes' if entity.get('is_leaf') else 'No'}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
"""
    else:
        html_content += """
        <div class="no-issues">
            ✓ No entities with zero revenue found. All entities have revenue data.
        </div>
"""
    
    html_content += f"""
        <h2>2. Accounts with Null Values</h2>
"""
    
    if null_account_entities:
        html_content += f"""
        <p>Found <strong>{len(null_account_entities)}</strong> entity-account combinations with null values.</p>
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th>Account</th>
                    <th>Parent</th>
                    <th>Level</th>
                </tr>
            </thead>
            <tbody>
"""
        for item in sorted(null_account_entities, key=lambda x: (x["entity"], x["account"])):
            html_content += f"""
                <tr>
                    <td>{item['entity']}</td>
                    <td>{item['account']}</td>
                    <td>{item.get('parent', 'N/A')}</td>
                    <td>{item['level']}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
"""
    else:
        html_content += """
        <div class="no-issues">
            ✓ No null account values found in key accounts. All key accounts have data.
        </div>
"""
    
    html_content += f"""
        <h2>3. Unbalanced Entities</h2>
"""
    
    if unbalanced_entities:
        html_content += f"""
        <p>Found <strong>{len(unbalanced_entities)}</strong> entities where Total Assets != Total Liabilities and Equity.</p>
        <p><strong>Balance Check:</strong> Total Assets vs Total Liabilities and Equity (Tolerance: ${BALANCE_TOLERANCE:.2f})</p>
        <p><strong>Note:</strong> Unbalanced means Assets != Liabilities + Equity (difference > tolerance)</p>
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th>Parent</th>
                    <th>Level</th>
                    <th>Total Assets</th>
                    <th>Total Liabilities & Equity</th>
                    <th>Difference</th>
                    <th>Is Leaf</th>
                </tr>
            </thead>
            <tbody>
"""
        for entity in sorted(unbalanced_entities, key=lambda x: (x["level"], -abs(x["difference"]))):
            diff_class = "negative" if entity["difference"] < 0 else "positive"
            html_content += f"""
                <tr>
                    <td>{entity['name']}</td>
                    <td>{entity.get('parent', 'N/A')}</td>
                    <td>{entity['level']}</td>
                    <td>${entity['assets']:,.2f}</td>
                    <td>${entity['liabilities_equity']:,.2f}</td>
                    <td class="{diff_class}">${entity['difference']:,.2f}</td>
                    <td>{'Yes' if entity.get('is_leaf') else 'No'}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
"""
    else:
        html_content += """
        <div class="no-issues">
            ✓ No unbalanced entities found. All entities are balanced (Assets = Liabilities + Equity).
        </div>
"""
    
    html_content += f"""
        <div class="footer">
            <p>Report generated by FCCS Data Quality Check Tool</p>
            <p>Generated: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(report_path)


async def run_data_quality_check():
    """Run comprehensive data quality check for FY24 Dec."""
    print("=" * 80)
    print("DATA QUALITY CHECK - FY24 DEC")
    print("=" * 80)
    print()
    print("Checks:")
    print("  1. Entities with zero revenue")
    print("  2. Accounts with null values")
    print("  3. Unbalanced entities (Assets != Liabilities + Equity)")
    print()
    
    # Initialize agent
    print("Initializing FCCS agent...")
    config = load_config()
    await initialize_agent(config)
    print("[OK] Agent initialized")
    print()
    
    # Load entities from cache
    print("Loading entities from cache...")
    entities = load_entity_hierarchy_from_cache()
    
    if not entities:
        print("[ERROR] No entities found in cache. Please ensure cache files exist.")
        await close_agent()
        return
    
    # Filter to leaf entities and level 1 (similar to unbalanced check)
    filtered_entities = [
        e for e in entities
        if e.get("is_leaf") or e.get("level") == 1
    ]
    
    print(f"[OK] Found {len(entities)} total entities")
    print(f"[OK] Filtered to {len(filtered_entities)} entities to check (leaf + level 1)")
    print()
    
    # Sort by level (bottom level first)
    filtered_entities.sort(key=lambda x: (x["level"], x["name"]))
    
    # 1. Check for zero revenue entities
    print("=" * 80)
    print("CHECK 1: Entities with Zero Revenue")
    print("=" * 80)
    print()
    print(f"Checking revenue (FCCS_Sales) for {len(filtered_entities)} entities...")
    print("(This may take several minutes)")
    print()
    
    zero_revenue_entities = []
    checked = 0
    
    for entity_info in filtered_entities:
        checked += 1
        entity_name = entity_info["name"]
        
        if checked % 20 == 0:
            print(f"  Progress: {checked}/{len(filtered_entities)} (Found {len(zero_revenue_entities)} with zero revenue)...")
        
        revenue = await get_revenue_value(entity_name)
        
        if revenue is None or abs(revenue) < 0.01:
            zero_revenue_entities.append({
                "name": entity_name,
                "level": entity_info["level"],
                "parent": entity_info.get("parent"),
                "is_leaf": entity_info.get("is_leaf"),
                "revenue": revenue if revenue is not None else 0.0
            })
    
    print()
    print(f"[OK] Found {len(zero_revenue_entities)} entities with zero revenue")
    print()
    
    # 2. Check for null account values
    print("=" * 80)
    print("CHECK 2: Accounts with Null Values")
    print("=" * 80)
    print()
    print(f"Checking key accounts for null values across {len(filtered_entities)} entities...")
    print(f"Key accounts: {', '.join(KEY_ACCOUNTS)}")
    print("(This may take several minutes)")
    print()
    
    null_account_entities = []
    checked = 0
    
    for entity_info in filtered_entities:
        checked += 1
        entity_name = entity_info["name"]
        
        if checked % 20 == 0:
            print(f"  Progress: {checked}/{len(filtered_entities)} (Found {len(null_account_entities)} null values)...")
        
        for account in KEY_ACCOUNTS:
            value = await get_account_value(account, entity_name)
            if value is None:
                null_account_entities.append({
                    "entity": entity_name,
                    "account": account,
                    "level": entity_info["level"],
                    "parent": entity_info.get("parent")
                })
    
    print()
    print(f"[OK] Found {len(null_account_entities)} entity-account combinations with null values")
    print()
    
    # 3. Check for unbalanced entities
    print("=" * 80)
    print("CHECK 3: Unbalanced Entities")
    print("=" * 80)
    print()
    print(f"Checking balance (Assets vs Liabilities + Equity) for {len(filtered_entities)} entities...")
    print("(This may take several minutes)")
    print()
    
    unbalanced_entities = []
    checked = 0
    entities_with_data = 0
    
    for entity_info in filtered_entities:
        checked += 1
        entity_name = entity_info["name"]
        
        if checked % 20 == 0:
            print(f"  Progress: {checked}/{len(filtered_entities)} (Found {len(unbalanced_entities)} unbalanced, {entities_with_data} with data)...")
        
        balance_values = await get_balance_sheet_values(entity_name)
        
        if balance_values is None:
            continue
        
        entities_with_data += 1
        assets, liabilities, difference = balance_values
        
        # Check if unbalanced (difference outside tolerance)
        if abs(difference) > BALANCE_TOLERANCE:
            unbalanced_entities.append({
                "name": entity_name,
                "level": entity_info["level"],
                "parent": entity_info.get("parent"),
                "is_leaf": entity_info.get("is_leaf"),
                "assets": assets,
                "liabilities_equity": liabilities,
                "difference": difference
            })
    
    print()
    print(f"[OK] Found {len(unbalanced_entities)} unbalanced entities")
    print(f"[OK] {entities_with_data} entities had balance sheet data")
    print()
    
    # Generate report
    print("=" * 80)
    print("GENERATING REPORT")
    print("=" * 80)
    print()
    
    report_path = generate_report(
        zero_revenue_entities,
        null_account_entities,
        unbalanced_entities,
        len(filtered_entities),
        entities_with_data
    )
    
    print(f"[OK] Report generated: {report_path}")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total entities checked: {len(filtered_entities)}")
    print(f"Entities with zero revenue: {len(zero_revenue_entities)}")
    print(f"Entity-account combinations with null values: {len(null_account_entities)}")
    print(f"Unbalanced entities: {len(unbalanced_entities)}")
    print()
    
    if len(zero_revenue_entities) == 0 and len(null_account_entities) == 0 and len(unbalanced_entities) == 0:
        print("✓ All data quality checks passed!")
    else:
        print("⚠ Data quality issues found. Please review the report.")
    
    print()
    
    await close_agent()


if __name__ == "__main__":
    asyncio.run(run_data_quality_check())

