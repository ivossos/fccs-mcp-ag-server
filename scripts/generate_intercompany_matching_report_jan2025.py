"""Generate Intercompany Matching Report for January 2025.

This script:
1. Loads ICO accounts from local file cache
2. Organizes them into debits and credits
3. Reports on level of entity
"""

import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import export_data_slice


def load_intercompany_accounts_from_csv(csv_path: Path) -> List[str]:
    """Load all intercompany accounts from Account metadata CSV.
    
    Returns list of account names that have Intercompany Account = IC_Acc_Yes
    """
    intercompany_accounts = []
    
    # Read CSV file - try utf-8-sig first (handles BOM)
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    rows = []
    fieldnames = None
    
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)
                if rows and fieldnames:
                    break
        except Exception as e:
            if encoding == encodings[-1]:
                raise
            continue
    
    if not rows or not fieldnames:
        return []
    
    # Find column name for Intercompany Account and Account
    interco_col = None
    account_col = None
    
    for field in fieldnames:
        field_stripped = field.strip()
        # Look for Intercompany Account column (may have leading space)
        if "Intercompany Account" in field_stripped and "CICTA" not in field_stripped:
            interco_col = field  # Keep original with spaces
        # Look for Account column (may have leading space)
        if field_stripped == "Account" or (field_stripped.startswith("Account") and "Type" not in field_stripped and "Alias" not in field_stripped):
            account_col = field  # Keep original with spaces
    
    if not interco_col or not account_col:
        print(f"  [WARNING] Could not find columns. Interco: {interco_col}, Account: {account_col}")
        print(f"  Available columns: {list(fieldnames)[:10]}...")
        return []
    
    # Extract intercompany accounts
    for row in rows:
        account_name = (row.get(account_col) or "").strip()
        interco_value = (row.get(interco_col) or "").strip()
        
        if account_name and interco_value and "IC_Acc_Yes" in interco_value:
            # Skip if it's a header or invalid account name
            if account_name != "Account" and account_name and account_name not in intercompany_accounts:
                intercompany_accounts.append(account_name)
    
    return intercompany_accounts


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


async def get_ico_account_value(
    account_name: str,
    entity_name: str,
    year: str = "FY25",
    period: str = "Jan"
) -> Optional[float]:
    """Get ICO account value for a specific entity and period."""
    try:
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
            "columns": [{"members": [[period]]}],
            "rows": [{"members": [[account_name]]}]
        }
        
        result = await export_data_slice(grid_definition, "Consol")
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                if value is not None:
                    return float(value)
    except Exception:
        pass
    return None


def generate_html_report(
    year: str,
    period: str,
    matched_pairs: List[Dict],
    unmatched_debits: List[Dict],
    unmatched_credits: List[Dict],
    summary_stats: Dict
) -> str:
    """Generate HTML report for intercompany matching with entity-partner pairs."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intercompany Matching Report - {year} {period}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .summary-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .summary-card .value.positive {{
            color: #28a745;
        }}
        
        .summary-card .value.negative {{
            color: #dc3545;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 0.9em;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            white-space: nowrap;
        }}
        
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .debit {{
            color: #28a745;
            font-weight: 600;
        }}
        
        .credit {{
            color: #dc3545;
            font-weight: 600;
        }}
        
        .account-name {{
            font-weight: 500;
            color: #495057;
            font-family: 'Courier New', monospace;
        }}
        
        .entity-name {{
            color: #667eea;
            font-weight: 500;
        }}
        
        .match-status {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85em;
        }}
        
        .match-status.matched {{
            background: #d4edda;
            color: #155724;
        }}
        
        .match-status.partial {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .match-status.unmatched {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .variance {{
            font-weight: 500;
        }}
        
        .variance.zero {{
            color: #28a745;
        }}
        
        .variance.small {{
            color: #ffc107;
        }}
        
        .variance.large {{
            color: #dc3545;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔗 Intercompany Matching Report - Level 0 Entities</h1>
            <p>{year} - {period}</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <div class="summary-card">
                    <h3>Total ICO Accounts</h3>
                    <div class="value">{summary_stats['total_accounts']}</div>
                </div>
                <div class="summary-card">
                    <h3>Matched Pairs</h3>
                    <div class="value positive">{summary_stats['matched_pairs']}</div>
                </div>
                <div class="summary-card">
                    <h3>Total Debits</h3>
                    <div class="value positive">${summary_stats['total_debits']:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>Total Credits</h3>
                    <div class="value negative">${summary_stats['total_credits']:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>Unmatched Debits</h3>
                    <div class="value negative">{summary_stats['unmatched_debits']}</div>
                </div>
                <div class="summary-card">
                    <h3>Unmatched Credits</h3>
                    <div class="value negative">{summary_stats['unmatched_credits']}</div>
                </div>
            </div>
"""
    
    # Add matched pairs section
    if matched_pairs:
        html += f"""
            <div class="section">
                <div class="section-header">✅ Matched Intercompany Pairs ({len(matched_pairs)})</div>
                <table>
                    <thead>
                        <tr>
                            <th>Entity</th>
                            <th>Account</th>
                            <th>Debit</th>
                            <th>Partner Entity</th>
                            <th>Partner Account</th>
                            <th>Credit</th>
                            <th>Match Status</th>
                            <th>Variance</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Sort by debit amount (largest first)
        sorted_pairs = sorted(matched_pairs, key=lambda x: x['debit'], reverse=True)
        
        for pair in sorted_pairs:
            variance_class = "zero" if pair['variance'] < 0.01 else ("small" if pair['variance'] < pair['debit'] * 0.05 else "large")
            match_class = "matched" if pair['match_status'] == "Matched" else "partial"
            
            html += f"""
                        <tr>
                            <td class="entity-name">{pair['entity']}</td>
                            <td class="account-name">{pair['account']}</td>
                            <td class="debit">${pair['debit']:,.2f}</td>
                            <td class="entity-name">{pair['partner_entity']}</td>
                            <td class="account-name">{pair['partner_account']}</td>
                            <td class="credit">${pair['credit']:,.2f}</td>
                            <td><span class="match-status {match_class}">{pair['match_status']}</span></td>
                            <td class="variance {variance_class}">${pair['variance']:,.2f}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
"""
    
    # Add unmatched debits section
    if unmatched_debits:
        html += f"""
            <div class="section">
                <div class="section-header">⚠️ Unmatched Debits ({len(unmatched_debits)})</div>
                <table>
                    <thead>
                        <tr>
                            <th>Entity</th>
                            <th>Account</th>
                            <th>Debit Amount</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        sorted_unmatched_debits = sorted(unmatched_debits, key=lambda x: x['debit'], reverse=True)
        
        for item in sorted_unmatched_debits:
            html += f"""
                        <tr>
                            <td class="entity-name">{item['entity']}</td>
                            <td class="account-name">{item['account']}</td>
                            <td class="debit">${item['debit']:,.2f}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
"""
    
    # Add unmatched credits section
    if unmatched_credits:
        html += f"""
            <div class="section">
                <div class="section-header">⚠️ Unmatched Credits ({len(unmatched_credits)})</div>
                <table>
                    <thead>
                        <tr>
                            <th>Entity</th>
                            <th>Account</th>
                            <th>Credit Amount</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        sorted_unmatched_credits = sorted(unmatched_credits, key=lambda x: x['credit'], reverse=True)
        
        for item in sorted_unmatched_credits:
            html += f"""
                        <tr>
                            <td class="entity-name">{item['entity']}</td>
                            <td class="account-name">{item['account']}</td>
                            <td class="credit">${item['credit']:,.2f}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
"""
    
    html += f"""
        </div>
        
        <div class="footer">
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def generate_intercompany_matching_report():
    """Generate intercompany matching report for January 2025."""
    print("=" * 80)
    print("INTERCOMPANY MATCHING REPORT - JANUARY 2025")
    print("=" * 80)
    print()
    
    year = "FY25"
    period = "Jan"
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Load ICO accounts from cache
        project_root = Path(__file__).parent.parent
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
        
        # Load entity hierarchy
        entity_csv_path = project_root / "Ravi_ExportedMetadata_Entity.csv"
        
        if not entity_csv_path.exists():
            print(f"[ERROR] Entity metadata file not found: {entity_csv_path}")
            await close_agent()
            return
        
        print(f"Loading entity hierarchy from: {entity_csv_path.name}")
        entities_map = load_entity_hierarchy_from_csv(entity_csv_path)
        print(f"[OK] Loaded {len(entities_map)} entities")
        print()
        
        # Filter entities to only Level 0 (leaf nodes) and exclude system entities
        exclude_keywords = [
            "FCCS_Global Assumptions", "FCCS_Entity Total", "Entity", 
            "FCCS_Total Geography", "FCCS_Intercompany Top"
        ]
        
        # Get only Level 0 entities (leaf nodes - entities with no children)
        level0_entities = []
        for name, info in entities_map.items():
            # Check if it's level 0 (no children) and not a system entity
            if (info.get("level", 0) == 0 and 
                len(info.get("children", [])) == 0 and
                not any(kw in name for kw in exclude_keywords)):
                level0_entities.append(name)
        
        valid_entities = level0_entities
        
        print(f"[OK] Found {len(valid_entities)} Level 0 (leaf) entities to query")
        if valid_entities:
            print(f"  Sample entities: {', '.join(valid_entities[:5])}...")
        print()
        
        # VALIDATION MODE: Query a few entities to find non-null amounts
        # Set to False for full report
        VALIDATION_MODE = True
        MAX_ENTITIES_TO_TEST = 20
        MAX_NON_NULL_TO_FIND = 5  # Stop after finding this many non-null values
        
        if VALIDATION_MODE:
            valid_entities = valid_entities[:MAX_ENTITIES_TO_TEST]
            print(f"[VALIDATION MODE] Testing first {len(valid_entities)} entities")
            print(f"  Will stop after finding {MAX_NON_NULL_TO_FIND} non-null amounts")
            print(f"  Testing entities: {', '.join(valid_entities[:10])}...")
            print()
        
        # Query data for each ICO account and entity
        print("Querying ICO account data...")
        if not VALIDATION_MODE:
            print("(This may take several minutes)")
        print()
        
        # Store all entity-account combinations
        entity_account_data = []  # List of {entity, account, value, debit, credit}
        total_debits = 0.0
        total_credits = 0.0
        total_queried = 0
        total_with_data = 0
        
        for account_idx, account_name in enumerate(intercompany_accounts, 1):
            print(f"Processing account {account_idx}/{len(intercompany_accounts)}: {account_name}")
            account_data_count = 0
            
            # In validation mode, stop early if we found enough data
            if VALIDATION_MODE and total_with_data >= MAX_NON_NULL_TO_FIND:
                print(f"  [VALIDATION] Found {total_with_data} non-null amounts. Stopping early.")
                break
            
            for entity_idx, entity_name in enumerate(valid_entities, 1):
                total_queried += 1
                
                value = await get_ico_account_value(
                    account_name,
                    entity_name,
                    year,
                    period
                )
                
                if value is not None and abs(value) > 0.01:
                    total_with_data += 1
                    account_data_count += 1
                    entity_info = entities_map.get(entity_name, {})
                    entity_level = entity_info.get("level", 0)
                    
                    # Only process Level 0 entities
                    if entity_level == 0:
                        # Separate debits (positive) and credits (negative)
                        if value > 0:
                            debit = value
                            credit = 0.0
                            total_debits += value
                            print(f"  [DEBIT] {entity_name} | {account_name} = ${value:,.2f}")
                        else:
                            debit = 0.0
                            credit = value  # negative value
                            total_credits += value
                            print(f"  [CREDIT] {entity_name} | {account_name} = ${value:,.2f}")
                        
                        entity_account_data.append({
                            "entity": entity_name,
                            "account": account_name,
                            "value": value,
                            "debit": debit,
                            "credit": credit,
                            "level": entity_level
                        })
                    
                    # In validation mode, stop after finding enough
                    if VALIDATION_MODE and total_with_data >= MAX_NON_NULL_TO_FIND:
                        print(f"  [VALIDATION] Found {total_with_data} non-null amounts. Stopping.")
                        break
                
                # Progress update every 10 entities in validation mode, 50 otherwise
                progress_interval = 10 if VALIDATION_MODE else 50
                if entity_idx % progress_interval == 0:
                    print(f"  Progress: {entity_idx}/{len(valid_entities)} entities queried, {account_data_count} with data so far...")
            
            print(f"  Account {account_name}: Found {account_data_count} entities with data")
            
            # In validation mode, stop after first account if we found data
            if VALIDATION_MODE and total_with_data > 0:
                print(f"  [VALIDATION] Found {total_with_data} non-null amounts total. Stopping after first account.")
                break
            
            print()
        
        # Match intercompany pairs
        print("Matching intercompany pairs...")
        matched_pairs = []
        unmatched_debits = []
        unmatched_credits = []
        
        # Create lookup: account -> list of entities with debits/credits
        debits_by_account = defaultdict(list)  # account -> [(entity, amount), ...]
        credits_by_account = defaultdict(list)  # account -> [(entity, amount), ...]
        
        for data in entity_account_data:
            if data['debit'] > 0:
                debits_by_account[data['account']].append((data['entity'], data['debit']))
            if data['credit'] < 0:
                credits_by_account[data['account']].append((data['entity'], abs(data['credit'])))
        
        # Match debits with credits for the same account
        for account in intercompany_accounts:
            debits = debits_by_account.get(account, [])
            credits = credits_by_account.get(account, [])
            
            # Try to match each debit with a credit
            matched_debit_indices = set()
            matched_credit_indices = set()
            
            for i, (debit_entity, debit_amount) in enumerate(debits):
                best_match = None
                best_match_idx = None
                best_variance = float('inf')
                
                for j, (credit_entity, credit_amount) in enumerate(credits):
                    if j in matched_credit_indices:
                        continue
                    
                    # Calculate variance (difference)
                    variance = abs(debit_amount - credit_amount)
                    
                    # Prefer exact matches or closest matches
                    if variance < best_variance:
                        best_match = (credit_entity, credit_amount)
                        best_match_idx = j
                        best_variance = variance
                
                if best_match and best_variance < debit_amount * 0.1:  # Match if within 10% variance
                    matched_pairs.append({
                        "entity": debit_entity,
                        "account": account,
                        "debit": debit_amount,
                        "partner_entity": best_match[0],
                        "partner_account": account,
                        "credit": best_match[1],
                        "variance": best_variance,
                        "match_status": "Matched" if best_variance < 0.01 else "Partial Match"
                    })
                    matched_debit_indices.add(i)
                    matched_credit_indices.add(best_match_idx)
                else:
                    unmatched_debits.append({
                        "entity": debit_entity,
                        "account": account,
                        "debit": debit_amount
                    })
            
            # Add unmatched credits
            for j, (credit_entity, credit_amount) in enumerate(credits):
                if j not in matched_credit_indices:
                    unmatched_credits.append({
                        "entity": credit_entity,
                        "account": account,
                        "credit": credit_amount
                    })
        
        print(f"[OK] Found {len(matched_pairs)} matched pairs")
        print(f"[OK] Found {len(unmatched_debits)} unmatched debits")
        print(f"[OK] Found {len(unmatched_credits)} unmatched credits")
        print()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total ICO Accounts: {len(intercompany_accounts)}")
        print(f"Total Entities Queried: {total_queried}")
        print(f"Data Points Found: {total_with_data}")
        print(f"Total Debits: ${total_debits:,.2f}")
        print(f"Total Credits: ${abs(total_credits):,.2f}")
        print(f"Matched Pairs: {len(matched_pairs)}")
        print(f"Unmatched Debits: {len(unmatched_debits)}")
        print(f"Unmatched Credits: {len(unmatched_credits)}")
        print()
        
        # Generate summary stats
        matched_debit_total = sum(p['debit'] for p in matched_pairs)
        matched_credit_total = sum(p['credit'] for p in matched_pairs)
        
        summary_stats = {
            "total_accounts": len(intercompany_accounts),
            "total_entities": total_with_data,
            "total_debits": total_debits,
            "total_credits": abs(total_credits),
            "matched_pairs": len(matched_pairs),
            "matched_debit_total": matched_debit_total,
            "matched_credit_total": matched_credit_total,
            "unmatched_debits": len(unmatched_debits),
            "unmatched_credits": len(unmatched_credits)
        }
        
        # Generate HTML report with matching pairs
        print("Generating HTML report with intercompany matches...")
        html_content = generate_html_report(
            year=year,
            period=period,
            matched_pairs=matched_pairs,
            unmatched_debits=unmatched_debits,
            unmatched_credits=unmatched_credits,
            summary_stats=summary_stats
        )
        
        # Save HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Intercompany_Matching_Report_{year}_{period}_{timestamp}.html"
        filepath = project_root / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[OK] Report saved to: {filename}")
        print()
        
        # Print summary for Level 0 entities
        print("=" * 80)
        print("LEVEL 0 ENTITIES SUMMARY")
        print("=" * 80)
        print()
        
        if matched_pairs or unmatched_debits or unmatched_credits:
            print(f"Level 0 Entities (Leaf Nodes):")
            print(f"  Matched Pairs: {len(matched_pairs)}")
            print(f"  Unmatched Debits: {len(unmatched_debits)}")
            print(f"  Unmatched Credits: {len(unmatched_credits)}")
            print()
            
            if matched_pairs:
                print("Sample Matched Pairs (Top 5):")
                for i, pair in enumerate(sorted(matched_pairs, key=lambda x: x['debit'], reverse=True)[:5], 1):
                    print(f"  {i}. {pair['entity']} ({pair['account']}) ${pair['debit']:,.2f} <-> "
                          f"{pair['partner_entity']} ({pair['partner_account']}) ${pair['credit']:,.2f} "
                          f"[{pair['match_status']}, Variance: ${pair['variance']:,.2f}]")
                print()
        else:
            print("No data found for Level 0 entities.")
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(generate_intercompany_matching_report())

