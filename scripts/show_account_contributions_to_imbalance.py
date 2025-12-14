"""Show which accounts are contributing to imbalanced entities for leaf level and 1 level above.

This script identifies unbalanced entities at leaf level (level 0) and level 1,
then shows which accounts are contributing to the imbalance.
"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache

# Tolerance for balance check
BALANCE_TOLERANCE = 0.01


def load_entity_hierarchy_from_csv(csv_path: Path) -> List[Dict]:
    """Load entity hierarchy from CSV metadata file."""
    entities_map = {}
    children_map = {}
    
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
    
    for row in rows:
        entity_name = (row.get("Entity") or row.get("\ufeffEntity") or row.get(" Entity") or "").strip()
        parent_name = (row.get(" Parent") or row.get("Parent") or "").strip()
        
        if not entity_name or entity_name == "Entity":
            continue
        
        entities_map[entity_name] = {
            "name": entity_name,
            "parent": parent_name if parent_name and parent_name != "Entity" else None,
            "children": []
        }
        
        if parent_name and parent_name != "Entity":
            if parent_name not in children_map:
                children_map[parent_name] = []
            children_map[parent_name].append(entity_name)
    
    for entity_name, entity_info in entities_map.items():
        if entity_name in children_map:
            entity_info["children"] = children_map[entity_name]
    
    if not entities_map:
        return []
    
    def calculate_level(entity_name: str, visited: set = None) -> int:
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


def get_account_children_from_cache(account_name: str) -> List[str]:
    """Get direct children of an account from the cache."""
    children = []
    cached_accounts = load_members_from_cache("Consol", "Account")
    
    if cached_accounts:
        items = cached_accounts.get("items", [])
        for item in items:
            parent = item.get("parent", "")
            name = item.get("name", "")
            
            # Check if this account is a child of the target account
            if account_name in parent or parent == account_name:
                if name and name != account_name:
                    children.append(name)
    
    return children


async def get_balance_sheet_values(entity_name: str, year: str = "FY24") -> Optional[Tuple[float, float, float]]:
    """Get balance sheet values for an entity."""
    try:
        assets_result = await smart_retrieve(
            account="FCCS_Total Assets",
            entity=entity_name,
            period="Dec",
            years=year,
            scenario="Actual"
        )
        
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
        
        if assets_value is None and liabilities_value is None:
            return None
        
        assets_value = assets_value if assets_value is not None else 0.0
        liabilities_value = liabilities_value if liabilities_value is not None else 0.0
        difference = assets_value - liabilities_value
        
        return (assets_value, liabilities_value, difference)
        
    except Exception as e:
        return None


async def get_account_values_for_entity(
    entity_name: str,
    account_names: List[str],
    year: str = "FY24"
) -> Dict[str, float]:
    """Get values for multiple accounts for a specific entity."""
    account_values = {}
    
    for account_name in account_names:
        try:
            result = await smart_retrieve(
                account=account_name,
                entity=entity_name,
                period="Dec",
                years=year,
                scenario="Actual"
            )
            
            if result.get("status") == "success":
                data = result.get("data", {})
                rows = data.get("rows", [])
                if rows and rows[0].get("data"):
                    value = rows[0]["data"][0]
                    if value is not None:
                        account_values[account_name] = float(value)
                    else:
                        account_values[account_name] = 0.0
                else:
                    account_values[account_name] = 0.0
            else:
                account_values[account_name] = 0.0
        except Exception:
            account_values[account_name] = 0.0
    
    return account_values


def generate_html_report(
    unbalanced_entities: List[Dict],
    sample_entities: List[Dict],
    account_contributions: List[Dict],
    level1_analysis: List[Dict],
    account_frequency: Dict[str, int]
) -> str:
    """Generate HTML report with account contributions and elimination analysis."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"Account_Contributions_Imbalance_Report_{timestamp}.html"
    project_root = Path(__file__).parent.parent
    
    leaf_entities = [e for e in unbalanced_entities if e["level"] == 0]
    level1_entities = [e for e in unbalanced_entities if e["level"] == 1]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Contributions to Imbalanced Entities Report</title>
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
        .negative {{
            color: #d32f2f;
        }}
        .positive {{
            color: #388e3c;
        }}
        .warning {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
        .info {{
            background-color: #d1ecf1;
            padding: 15px;
            border-left: 4px solid #17a2b8;
            margin: 15px 0;
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
        <h1>Account Contributions to Imbalanced Entities Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        <p><strong>Report Period:</strong> FY24 (December YTD)</p>
        <p><strong>Focus:</strong> Leaf Level (0) and Level 1 Entities</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <strong>Total Unbalanced Entities</strong>
                    <span>{len(unbalanced_entities)}</span>
                </div>
                <div class="summary-item">
                    <strong>Leaf Level (0) Unbalanced</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(leaf_entities)}</span>
                </div>
                <div class="summary-item">
                    <strong>Level 1 Unbalanced</strong>
                    <span style="color: #d32f2f; font-weight: bold;">{len(level1_entities)}</span>
                </div>
                <div class="summary-item">
                    <strong>Sample Analyzed</strong>
                    <span>{len(sample_entities)}</span>
                </div>
            </div>
        </div>
        
        <h2>Level 1 Elimination Analysis</h2>
"""
    
    # Add level 1 elimination analysis
    if level1_analysis:
        entities_with_missing_elim = [a for a in level1_analysis if abs(a["potential_missing_elimination"]) > 1000]
        
        if entities_with_missing_elim:
            html_content += f"""
        <div class="warning">
            <strong>WARNING:</strong> {len(entities_with_missing_elim)} Level 1 entities show potential missing eliminations
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th style="text-align: right;">Parent Imbalance</th>
                    <th style="text-align: right;">Child Imbalance Total</th>
                    <th style="text-align: right;">Potential Missing Elimination</th>
                    <th>Unbalanced Children</th>
                </tr>
            </thead>
            <tbody>
"""
            for analysis in sorted(entities_with_missing_elim, key=lambda x: abs(x["potential_missing_elimination"]), reverse=True):
                elim_class = "negative" if analysis["potential_missing_elimination"] < 0 else "positive"
                children_info = f"{analysis['unbalanced_children_count']}/{analysis['total_children_count']}"
                html_content += f"""
                <tr>
                    <td>{analysis['entity']}</td>
                    <td style="text-align: right;">${analysis['parent_imbalance']:,.2f}</td>
                    <td style="text-align: right;">${analysis['child_imbalance_total']:,.2f}</td>
                    <td style="text-align: right;" class="{elim_class}"><strong>${analysis['potential_missing_elimination']:,.2f}</strong></td>
                    <td>{children_info}</td>
                </tr>
"""
            html_content += """
            </tbody>
        </table>
"""
        else:
            html_content += """
        <div class="info">
            No significant missing eliminations detected in Level 1 entities.
        </div>
"""
    
    # Add sample entity analysis
    html_content += """
        <h2>Sample Entity Analysis</h2>
        <p>Top entities by largest imbalance with account-level breakdown:</p>
        <table>
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th>Level</th>
                    <th style="text-align: right;">Assets</th>
                    <th style="text-align: right;">Liab + Equity</th>
                    <th style="text-align: right;">Difference</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for entity in sorted(sample_entities, key=lambda x: abs(x["difference"]), reverse=True):
        diff_class = "negative" if entity["difference"] < 0 else "positive"
        level_label = "LEAF" if entity["level"] == 0 else "LEVEL 1"
        html_content += f"""
                <tr>
                    <td><strong>{entity['name']}</strong></td>
                    <td>{level_label}</td>
                    <td style="text-align: right;">${entity['assets']:,.2f}</td>
                    <td style="text-align: right;">${entity['liabilities_equity']:,.2f}</td>
                    <td style="text-align: right;" class="{diff_class}"><strong>${entity['difference']:,.2f}</strong></td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Top Contributing Accounts</h2>
        <table>
            <thead>
                <tr>
                    <th>Account Name</th>
                    <th style="text-align: right;">Frequency</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for account, freq in sorted(account_frequency.items(), key=lambda x: x[1], reverse=True)[:15]:
        html_content += f"""
                <tr>
                    <td>{account}</td>
                    <td style="text-align: right;"><strong>{freq}</strong></td>
                </tr>
"""
    
    html_content += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>FCCS Account Contributions to Imbalanced Entities Report</strong></p>
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


async def analyze_account_contributions():
    """Analyze which accounts contribute to imbalances for leaf and level 1 entities."""
    print("=" * 80)
    print("ACCOUNT CONTRIBUTIONS TO IMBALANCED ENTITIES")
    print("Analyzing Leaf Level (0) and Level 1 entities")
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
        all_entities = load_entity_hierarchy_from_csv(entity_csv_path)
        
        if not all_entities:
            print("[ERROR] No entities loaded from CSV file")
            await close_agent()
            return
        
        print(f"[OK] Loaded {len(all_entities)} entities from CSV")
        print()
        
        # Filter for leaf level (0) and level 1 entities
        exclude_keywords = ["FCCS_Global Assumptions", "FCCS_Entity Total", "Entity"]
        target_entities = [
            e for e in all_entities 
            if e["level"] <= 1 and not any(kw in e["name"] for kw in exclude_keywords)
        ]
        
        print(f"[OK] Found {len(target_entities)} entities at leaf level (0) and level 1")
        print(f"  - Leaf level (0): {sum(1 for e in target_entities if e['level'] == 0)}")
        print(f"  - Level 1: {sum(1 for e in target_entities if e['level'] == 1)}")
        print()
        
        # Check balance for each entity
        print("Checking balance for each entity...")
        print("(This may take several minutes)")
        print()
        
        unbalanced_entities = []
        checked = 0
        
        for entity_info in target_entities:
            checked += 1
            entity_name = entity_info["name"]
            
            if checked % 10 == 0:
                print(f"  Progress: {checked}/{len(target_entities)} (Found {len(unbalanced_entities)} unbalanced)...")
            
            balance_values = await get_balance_sheet_values(entity_name, "FY24")
            
            if balance_values is None:
                continue
            
            assets, liabilities, difference = balance_values
            
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
        print(f"[OK] Found {len(unbalanced_entities)} unbalanced entities")
        print()
        
        if not unbalanced_entities:
            print("No unbalanced entities found at leaf level and level 1!")
            await close_agent()
            return
        
        # Sample a few entities for analysis (top 10 by absolute imbalance)
        unbalanced_entities_sorted = sorted(unbalanced_entities, key=lambda x: abs(x["difference"]), reverse=True)
        sample_size = min(10, len(unbalanced_entities_sorted))
        sample_entities = unbalanced_entities_sorted[:sample_size]
        
        print(f"Sampling {sample_size} entities with largest imbalances for detailed analysis...")
        print(f"(Total unbalanced: {len(unbalanced_entities)})")
        print()
        
        # Get child accounts of Total Assets and Total Liabilities and Equity
        print("Finding child accounts from cache...")
        
        # Get children from cache
        assets_children = get_account_children_from_cache("FCCS_Total Assets")
        liabilities_children = get_account_children_from_cache("FCCS_Total Liabilities and Equity")
        
        # Also try alternative names
        if not assets_children:
            assets_children = get_account_children_from_cache("Total Assets")
        if not liabilities_children:
            liabilities_children = get_account_children_from_cache("Total Liabilities and Equity")
            if not liabilities_children:
                liabilities_children = get_account_children_from_cache("Total Liabilities")
        
        # If still no children, try to get common balance sheet accounts from cache
        if not assets_children or not liabilities_children:
            print("  Searching for common balance sheet accounts...")
            cached_accounts = load_members_from_cache("Consol", "Account")
            if cached_accounts:
                items = cached_accounts.get("items", [])
                
                # Common asset account keywords
                asset_keywords = ["Asset", "Cash", "Receivable", "Inventory", "Property", "Equipment", 
                                 "Investment", "Prepaid", "Intangible", "Goodwill"]
                
                # Common liability/equity keywords
                liability_keywords = ["Liability", "Payable", "Debt", "Loan", "Equity", "Capital", 
                                     "Retained", "Earnings", "Accrued", "Deferred"]
                
                for item in items:
                    name = item.get("name", "").lower()
                    parent = item.get("parent", "").lower()
                    
                    # Check if it's likely an asset account
                    if any(kw.lower() in name or kw.lower() in parent for kw in asset_keywords):
                        if name not in [a.lower() for a in assets_children]:
                            assets_children.append(item.get("name"))
                    
                    # Check if it's likely a liability/equity account
                    if any(kw.lower() in name or kw.lower() in parent for kw in liability_keywords):
                        if name not in [l.lower() for l in liabilities_children]:
                            liabilities_children.append(item.get("name"))
        
        # Limit to top 40 accounts to avoid too many API calls
        assets_children = assets_children[:40]
        liabilities_children = liabilities_children[:40]
        
        print(f"  Found {len(assets_children)} asset accounts and {len(liabilities_children)} liability/equity accounts")
        if assets_children:
            print(f"  Sample asset accounts: {', '.join(assets_children[:5])}")
        if liabilities_children:
            print(f"  Sample liability/equity accounts: {', '.join(liabilities_children[:5])}")
        print()
        
        # Analyze each unbalanced entity (sample only)
        print("=" * 80)
        print("ANALYZING ACCOUNT CONTRIBUTIONS (SAMPLE)")
        print("=" * 80)
        print()
        
        all_account_contributions = []
        
        for i, entity in enumerate(sample_entities, 1):
            entity_name = entity["name"]
            level_label = "LEAF" if entity["level"] == 0 else "LEVEL 1"
            
            print(f"[{i}/{len(unbalanced_entities)}] {entity_name} ({level_label})")
            print(f"  Assets: ${entity['assets']:,.2f}")
            print(f"  Liabilities + Equity: ${entity['liabilities_equity']:,.2f}")
            print(f"  Difference: ${entity['difference']:,.2f}")
            print()
            
            # Get account values
            print("  Retrieving account values...")
            asset_account_values = await get_account_values_for_entity(
                entity_name, assets_children, "FY24"
            )
            liability_account_values = await get_account_values_for_entity(
                entity_name, liabilities_children, "FY24"
            )
            
            # Calculate total from accounts
            total_assets_from_accounts = sum(asset_account_values.values())
            total_liabilities_from_accounts = sum(liability_account_values.values())
            
            # Calculate the expected balance
            expected_balance = total_assets_from_accounts - total_liabilities_from_accounts
            actual_difference = entity["difference"]
            
            # Calculate missing amount (accounts might not sum to total due to missing accounts)
            missing_from_accounts = actual_difference - expected_balance
            
            print(f"  Total from asset accounts: ${total_assets_from_accounts:,.2f}")
            print(f"  Total from liability/equity accounts: ${total_liabilities_from_accounts:,.2f}")
            print(f"  Expected difference (from accounts): ${expected_balance:,.2f}")
            print(f"  Actual difference (from totals): ${actual_difference:,.2f}")
            if abs(missing_from_accounts) > 100:
                print(f"  [WARNING] Missing/unaccounted amount: ${missing_from_accounts:,.2f}")
            print()
            
            # Find accounts with significant values
            significant_accounts = []
            
            # Asset accounts
            for account_name, value in sorted(asset_account_values.items(), key=lambda x: abs(x[1]), reverse=True):
                if abs(value) > 1000:  # Only show accounts with significant values
                    significant_accounts.append({
                        "account": account_name,
                        "value": value,
                        "type": "Asset"
                    })
            
            # Liability/Equity accounts
            for account_name, value in sorted(liability_account_values.items(), key=lambda x: abs(x[1]), reverse=True):
                if abs(value) > 1000:  # Only show accounts with significant values
                    significant_accounts.append({
                        "account": account_name,
                        "value": value,
                        "type": "Liability/Equity"
                    })
            
            # Show top contributing accounts
            print("  Top contributing accounts:")
            for acc in significant_accounts[:10]:  # Show top 10
                acc_type = acc["type"]
                value = acc["value"]
                print(f"    {acc['account']:<50} ({acc_type}): ${value:>15,.2f}")
            
            all_account_contributions.append({
                "entity": entity_name,
                "level": entity["level"],
                "difference": actual_difference,
                "accounts": significant_accounts
            })
            
            print()
        
        # Build entity map for finding children (need to rebuild from CSV structure)
        entity_map_for_children = {}
        for e in all_entities:
            entity_map_for_children[e["name"]] = e
        
        # Analyze level 1 entities for missing eliminations
        print("=" * 80)
        print("CHECKING LEVEL 1 ENTITIES FOR MISSING ELIMINATIONS")
        print("=" * 80)
        print()
        
        level1_analysis = []
        level1_entities_list = [e for e in unbalanced_entities if e["level"] == 1]
        
        for level1_entity in level1_entities_list:
            entity_name = level1_entity["name"]
            entity_info = entity_map_for_children.get(entity_name, {})
            # Get children from the original CSV load
            children = []
            for e in all_entities:
                if e.get("parent") == entity_name:
                    children.append(e["name"])
            
            if not children:
                continue
            
            # Find which children are unbalanced
            unbalanced_children = []
            child_imbalance_total = 0.0
            
            for child_name in children:
                child_entity = next((e for e in unbalanced_entities if e["name"] == child_name), None)
                if child_entity:
                    unbalanced_children.append({
                        "name": child_name,
                        "difference": child_entity["difference"]
                    })
                    child_imbalance_total += child_entity["difference"]
            
            # Check for intercompany elimination accounts
            elimination_accounts = []
            cached_accounts = load_members_from_cache("Consol", "Account")
            if cached_accounts:
                items = cached_accounts.get("items", [])
                for item in items:
                    name = item.get("name", "").lower()
                    if any(term in name for term in ["elimination", "intercompany", "ic", "consolidation", "adjustment"]):
                        elimination_accounts.append(item.get("name"))
            
            # Calculate if imbalance could be from missing eliminations
            parent_imbalance = level1_entity["difference"]
            potential_missing_elimination = parent_imbalance - child_imbalance_total
            
            level1_analysis.append({
                "entity": entity_name,
                "parent_imbalance": parent_imbalance,
                "unbalanced_children_count": len(unbalanced_children),
                "total_children_count": len(children),
                "child_imbalance_total": child_imbalance_total,
                "potential_missing_elimination": potential_missing_elimination,
                "unbalanced_children": unbalanced_children,
                "elimination_accounts_found": len(elimination_accounts) > 0
            })
            
            if len(unbalanced_children) > 0 or abs(potential_missing_elimination) > 1000:
                print(f"{entity_name}:")
                print(f"  Parent imbalance: ${parent_imbalance:,.2f}")
                print(f"  Unbalanced children: {len(unbalanced_children)}/{len(children)}")
                if unbalanced_children:
                    print(f"  Total child imbalances: ${child_imbalance_total:,.2f}")
                    print(f"  Potential missing elimination: ${potential_missing_elimination:,.2f}")
                print()
        
        # Generate summary report
        print("=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)
        print()
        
        # Group by level (all unbalanced entities)
        leaf_entities = [e for e in unbalanced_entities if e["level"] == 0]
        level1_entities = [e for e in unbalanced_entities if e["level"] == 1]
        
        print(f"Leaf Level (0) Unbalanced Entities: {len(leaf_entities)}")
        print(f"  Total imbalance: ${sum(e['difference'] for e in leaf_entities):,.2f}")
        print()
        print(f"Level 1 Unbalanced Entities: {len(level1_entities)}")
        print(f"  Total imbalance: ${sum(e['difference'] for e in level1_entities):,.2f}")
        print()
        print(f"Sample analyzed: {len(sample_entities)} entities")
        print()
        
        # Level 1 elimination analysis summary
        if level1_analysis:
            print("Level 1 Elimination Analysis:")
            entities_with_unbalanced_children = [a for a in level1_analysis if a["unbalanced_children_count"] > 0]
            entities_with_potential_missing_elim = [a for a in level1_analysis if abs(a["potential_missing_elimination"]) > 1000]
            
            print(f"  Level 1 entities with unbalanced children: {len(entities_with_unbalanced_children)}")
            print(f"  Level 1 entities with potential missing eliminations: {len(entities_with_potential_missing_elim)}")
            if entities_with_potential_missing_elim:
                total_potential_missing = sum(a["potential_missing_elimination"] for a in entities_with_potential_missing_elim)
                print(f"  Total potential missing eliminations: ${total_potential_missing:,.2f}")
            print()
        
        # Find most common accounts in imbalances
        account_frequency = defaultdict(int)
        for contrib in all_account_contributions:
            for acc in contrib["accounts"]:
                if abs(acc["value"]) > 1000:
                    account_frequency[acc["account"]] += 1
        
        if account_frequency:
            print("Most frequently appearing accounts in imbalances:")
            for account, freq in sorted(account_frequency.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {account}: appears in {freq} unbalanced entities")
        
        # Generate HTML report
        print()
        print("=" * 80)
        print("GENERATING REPORT")
        print("=" * 80)
        report_path = generate_html_report(
            unbalanced_entities,
            sample_entities,
            all_account_contributions,
            level1_analysis,
            account_frequency
        )
        print(f"[OK] Report generated: {report_path}")
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(analyze_account_contributions())

