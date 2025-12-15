"""Analyze Level 1 entities for equity elimination issues in 2025.

This script identifies Level 1 entities where:
1. Parent has "FCCS_Investment In Sub" balances
2. Subsidiary equity accounts exist but are not properly eliminated
3. Missing or incomplete equity eliminations causing imbalances
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


# Tolerance for matching investment vs equity
MATCH_TOLERANCE = 0.01


def load_entity_hierarchy_from_csv(csv_path: Path) -> Dict[str, Dict]:
    """Load entity hierarchy from CSV metadata file.
    
    Returns dict mapping entity_name -> entity_info with children.
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
    
    return entities_map


async def get_account_value(entity_name: str, account: str, year: str = "FY25") -> Optional[float]:
    """Get account value for an entity."""
    try:
        result = await smart_retrieve(
            account=account,
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
                    return float(value)
        return None
    except Exception:
        return None


async def get_equity_accounts(entity_name: str, year: str = "FY25") -> Dict[str, float]:
    """Get all equity-related accounts for an entity."""
    equity_accounts = {
        "FCCS_Investment In Sub": None,
        "FCCS_Total Equity": None,
        "FCCS_Retained Earnings": None,
        "FCCS_Common Stock": None,
        "FCCS_Additional Paid In Capital": None,
        "FCCS_CTA": None,
        "FCCS_Retained Earnings Prior": None,
        "FCCS_Retained Earnings Current": None,
    }
    
    for account in equity_accounts.keys():
        value = await get_account_value(entity_name, account, year)
        equity_accounts[account] = value if value is not None else 0.0
    
    return equity_accounts


async def analyze_level1_equity_eliminations():
    """Analyze Level 1 entities for equity elimination issues."""
    print("=" * 80)
    print("LEVEL 1 ENTITIES - EQUITY ELIMINATION ANALYSIS (2025)")
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
        
        # Get Level 1 entities (entities that have children but are not at bottom level)
        # We'll identify them by having children
        level1_entities = []
        for entity_name, entity_info in entities_map.items():
            children = entity_info.get("children", [])
            if children:
                # Check if it's likely Level 1 (has children that are likely leaf nodes)
                # For now, we'll get all entities with children
                level1_entities.append({
                    "name": entity_name,
                    "children": children,
                    "parent": entity_info.get("parent")
                })
        
        # Filter out system entities
        exclude_keywords = ["FCCS_Global Assumptions", "FCCS_Entity Total", "Entity", "FCCS_Total Geography"]
        filtered_level1 = [
            e for e in level1_entities
            if not any(kw in e["name"] for kw in exclude_keywords)
        ]
        
        print(f"[OK] Found {len(filtered_level1)} Level 1 entities to analyze")
        print()
        
        # Analyze each Level 1 entity
        print("Analyzing equity elimination issues...")
        print("(This may take several minutes)")
        print()
        
        issues_found = []
        checked = 0
        
        for entity_info in filtered_level1:
            checked += 1
            entity_name = entity_info["name"]
            children = entity_info["children"]
            
            if checked % 5 == 0:
                print(f"  Progress: {checked}/{len(filtered_level1)} (Found {len(issues_found)} issues)...")
            
            # Get parent's investment in sub account
            parent_equity = await get_equity_accounts(entity_name, "FY25")
            parent_investment = parent_equity.get("FCCS_Investment In Sub", 0.0)
            
            # If parent has investment, check children's equity
            if abs(parent_investment) > MATCH_TOLERANCE:
                # Get children's total equity
                children_equity_total = 0.0
                children_details = []
                
                for child_name in children[:10]:  # Limit to first 10 children to avoid timeout
                    child_equity = await get_equity_accounts(child_name, "FY25")
                    child_total_equity = child_equity.get("FCCS_Total Equity", 0.0)
                    child_retained_earnings = child_equity.get("FCCS_Retained Earnings", 0.0)
                    child_common_stock = child_equity.get("FCCS_Common Stock", 0.0)
                    
                    if abs(child_total_equity) > MATCH_TOLERANCE or abs(child_retained_earnings) > MATCH_TOLERANCE:
                        children_equity_total += child_total_equity
                        children_details.append({
                            "name": child_name,
                            "total_equity": child_total_equity,
                            "retained_earnings": child_retained_earnings,
                            "common_stock": child_common_stock
                        })
                
                # Check if investment matches equity (within tolerance)
                difference = abs(parent_investment) - abs(children_equity_total)
                
                if abs(difference) > MATCH_TOLERANCE:
                    # Potential equity elimination issue
                    issues_found.append({
                        "parent": entity_name,
                        "parent_investment": parent_investment,
                        "children_equity_total": children_equity_total,
                        "difference": difference,
                        "children_count": len(children),
                        "children_details": children_details[:5]  # Limit details
                    })
            else:
                # Check if children have equity but parent has no investment
                # This could indicate missing investment recording
                children_with_equity = []
                for child_name in children[:5]:  # Limit check
                    child_equity = await get_equity_accounts(child_name, "FY25")
                    child_total_equity = child_equity.get("FCCS_Total Equity", 0.0)
                    if abs(child_total_equity) > MATCH_TOLERANCE:
                        children_with_equity.append({
                            "name": child_name,
                            "total_equity": child_total_equity
                        })
                
                if children_with_equity:
                    issues_found.append({
                        "parent": entity_name,
                        "parent_investment": 0.0,
                        "children_equity_total": sum(c["total_equity"] for c in children_with_equity),
                        "difference": sum(c["total_equity"] for c in children_with_equity),
                        "children_count": len(children),
                        "issue_type": "Missing Investment Recording",
                        "children_details": children_with_equity
                    })
        
        print()
        print("=" * 80)
        print("RESULTS - EQUITY ELIMINATION ISSUES AT LEVEL 1")
        print("=" * 80)
        print()
        
        if not issues_found:
            print("✓ No equity elimination issues found at Level 1!")
        else:
            print(f"Found {len(issues_found)} Level 1 entities with equity elimination issues:")
            print()
            
            # Sort by difference (largest first)
            issues_found.sort(key=lambda x: abs(x.get("difference", 0)), reverse=True)
            
            for i, issue in enumerate(issues_found, 1):
                parent = issue["parent"]
                parent_inv = issue["parent_investment"]
                children_eq = issue["children_equity_total"]
                diff = issue["difference"]
                issue_type = issue.get("issue_type", "Investment/Equity Mismatch")
                
                print(f"{i}. {parent}")
                print(f"   Issue Type: {issue_type}")
                print(f"   Parent Investment In Sub: ${parent_inv:,.2f}")
                print(f"   Children Total Equity: ${children_eq:,.2f}")
                print(f"   Difference (Potential Elimination Gap): ${diff:,.2f}")
                print(f"   Number of Children: {issue['children_count']}")
                
                if issue.get("children_details"):
                    print(f"   Sample Children with Equity:")
                    for child in issue["children_details"][:3]:
                        child_name = child["name"]
                        child_eq = child.get("total_equity", 0.0)
                        print(f"      - {child_name}: ${child_eq:,.2f}")
                
                print()
            
            # Generate detailed report
            print("=" * 80)
            print("GENERATING DETAILED REPORT")
            print("=" * 80)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"Level1_Equity_Elimination_Issues_2025_{timestamp}.html"
            report_path = project_root / report_filename
            
            html_content = generate_html_report(issues_found, timestamp)
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"[OK] Report generated: {report_filename}")
            print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_html_report(issues: List[Dict], timestamp: str) -> str:
    """Generate HTML report for equity elimination issues."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Level 1 Equity Elimination Issues - 2025</title>
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
        .issue-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .issue-box h3 {{
            margin-top: 0;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Level 1 Entities - Equity Elimination Issues (2025)</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
        <p><strong>Report Period:</strong> FY25 (December YTD)</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <p><strong>Total Level 1 Entities Analyzed:</strong> {len(issues)}</p>
            <p><strong>Entities with Equity Elimination Issues:</strong> {len(issues)}</p>
        </div>
        
        <h2>Equity Elimination Issues Identified</h2>
        <p>The following Level 1 entities show potential equity elimination problems:</p>
"""
    
    for i, issue in enumerate(issues, 1):
        parent = issue["parent"]
        parent_inv = issue["parent_investment"]
        children_eq = issue["children_equity_total"]
        diff = issue["difference"]
        issue_type = issue.get("issue_type", "Investment/Equity Mismatch")
        children_count = issue["children_count"]
        
        diff_class = "negative" if diff < 0 else "positive"
        
        html_content += f"""
        <div class="issue-box">
            <h3>{i}. {parent}</h3>
            <table>
                <tr>
                    <th>Issue Type</th>
                    <td><strong>{issue_type}</strong></td>
                </tr>
                <tr>
                    <th>Parent Investment In Sub</th>
                    <td>${parent_inv:,.2f}</td>
                </tr>
                <tr>
                    <th>Children Total Equity</th>
                    <td>${children_eq:,.2f}</td>
                </tr>
                <tr>
                    <th>Difference (Elimination Gap)</th>
                    <td class="{diff_class}"><strong>${diff:,.2f}</strong></td>
                </tr>
                <tr>
                    <th>Number of Children</th>
                    <td>{children_count}</td>
                </tr>
            </table>
"""
        
        if issue.get("children_details"):
            html_content += """
            <h4>Children with Equity:</h4>
            <table>
                <thead>
                    <tr>
                        <th>Child Entity</th>
                        <th style="text-align: right;">Total Equity</th>
                        <th style="text-align: right;">Retained Earnings</th>
                        <th style="text-align: right;">Common Stock</th>
                    </tr>
                </thead>
                <tbody>
"""
            for child in issue["children_details"]:
                child_name = child["name"]
                child_eq = child.get("total_equity", 0.0)
                child_re = child.get("retained_earnings", 0.0)
                child_cs = child.get("common_stock", 0.0)
                
                html_content += f"""
                    <tr>
                        <td>{child_name}</td>
                        <td style="text-align: right;">${child_eq:,.2f}</td>
                        <td style="text-align: right;">${child_re:,.2f}</td>
                        <td style="text-align: right;">${child_cs:,.2f}</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
"""
        
        html_content += """
        </div>
"""
    
    html_content += f"""
        <div class="summary">
            <h2>Recommended Actions</h2>
            <ol>
                <li><strong>Review Investment Eliminations:</strong>
                    <ul>
                        <li>Verify that "FCCS_Investment In Sub" accounts are being eliminated against subsidiary equity</li>
                        <li>Check elimination journals are posted for all periods</li>
                        <li>Confirm elimination calculations match subsidiary equity balances</li>
                    </ul>
                </li>
                <li><strong>Validate Equity Accounts:</strong>
                    <ul>
                        <li>Review retained earnings rollforward for all entities</li>
                        <li>Verify net income is flowing to retained earnings correctly</li>
                        <li>Check for missing prior period adjustments</li>
                    </ul>
                </li>
                <li><strong>Check Consolidation Rules:</strong>
                    <ul>
                        <li>Verify consolidation business rules are running correctly</li>
                        <li>Check that elimination rules are applied to all relevant entities</li>
                        <li>Review data storage and calculation settings for equity accounts</li>
                    </ul>
                </li>
            </ol>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e0e0e0; text-align: center; color: #666; font-size: 12px;">
            <p><strong>FCCS Level 1 Equity Elimination Analysis</strong></p>
            <p>Data from Oracle EPM Cloud Financial Consolidation and Close (FCCS)</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


if __name__ == "__main__":
    asyncio.run(analyze_level1_equity_eliminations())

