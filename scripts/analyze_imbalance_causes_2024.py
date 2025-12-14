"""Analyze what contributes to balance sheet imbalances for 2024.

This script analyzes patterns and potential causes of balance sheet imbalances.
"""

import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


BALANCE_TOLERANCE = 0.01


def load_entity_hierarchy_from_csv(csv_path: Path) -> Dict[str, Dict]:
    """Load entity hierarchy and return as a map."""
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
        except Exception:
            if encoding == encodings[-1]:
                raise
            continue
    
    for row in rows:
        entity_name = (row.get("Entity") or row.get("\ufeffEntity") or "").strip()
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
    
    return entities_map


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
        
    except Exception:
        return None


async def analyze_imbalance_causes():
    """Analyze what contributes to balance sheet imbalances."""
    print("=" * 80)
    print("ANALYZING IMBALANCE CAUSES - 2024")
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
        entities_map = load_entity_hierarchy_from_csv(entity_csv_path)
        
        exclude_keywords = ["FCCS_Global Assumptions", "FCCS_Entity Total", "Entity"]
        entities_to_check = [
            name for name in entities_map.keys()
            if not any(kw in name for kw in exclude_keywords)
        ]
        
        print(f"Analyzing {len(entities_to_check)} entities...")
        print("(This may take several minutes)")
        print()
        
        # Collect balance data
        entity_balances = {}
        checked = 0
        
        for entity_name in entities_to_check:
            checked += 1
            if checked % 50 == 0:
                print(f"  Progress: {checked}/{len(entities_to_check)}...")
            
            balance = await get_balance_sheet_values(entity_name, "FY24")
            if balance:
                assets, liabilities, difference = balance
                if abs(difference) > BALANCE_TOLERANCE:
                    entity_info = entities_map.get(entity_name, {})
                    entity_balances[entity_name] = {
                        "assets": assets,
                        "liabilities": liabilities,
                        "difference": difference,
                        "parent": entity_info.get("parent"),
                        "children": entity_info.get("children", [])
                    }
        
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print()
        
        if not entity_balances:
            print("No unbalanced entities found for analysis.")
            await close_agent()
            return
        
        # Analysis 1: Direction of imbalances
        print("1. DIRECTION OF IMBALANCES")
        print("-" * 80)
        positive_imbalances = [e for e in entity_balances.values() if e["difference"] > 0]
        negative_imbalances = [e for e in entity_balances.values() if e["difference"] < 0]
        
        print(f"Entities with Assets > Liabilities + Equity: {len(positive_imbalances)}")
        print(f"  Total excess: ${sum(e['difference'] for e in positive_imbalances):,.2f}")
        print(f"Entities with Assets < Liabilities + Equity: {len(negative_imbalances)}")
        print(f"  Total deficit: ${abs(sum(e['difference'] for e in negative_imbalances)):,.2f}")
        print()
        
        # Analysis 2: Parent-Child Relationships
        print("2. PARENT-CHILD RELATIONSHIP ANALYSIS")
        print("-" * 80)
        parent_child_issues = []
        for entity_name, data in entity_balances.items():
            parent = data["parent"]
            if parent and parent in entity_balances:
                parent_diff = entity_balances[parent]["difference"]
                child_diff = data["difference"]
                parent_child_issues.append({
                    "parent": parent,
                    "child": entity_name,
                    "parent_diff": parent_diff,
                    "child_diff": child_diff,
                    "combined": parent_diff + child_diff
                })
        
        if parent_child_issues:
            print(f"Found {len(parent_child_issues)} parent-child pairs where both are unbalanced")
            print("\nTop 10 parent-child pairs with largest combined imbalances:")
            sorted_issues = sorted(parent_child_issues, key=lambda x: abs(x["combined"]), reverse=True)[:10]
            for i, issue in enumerate(sorted_issues, 1):
                print(f"  {i}. Parent: {issue['parent']} (${issue['parent_diff']:,.2f})")
                print(f"     Child: {issue['child']} (${issue['child_diff']:,.2f})")
                print(f"     Combined: ${issue['combined']:,.2f}")
        else:
            print("No parent-child pairs found where both are unbalanced")
        print()
        
        # Analysis 3: Cumulative Effect Analysis
        print("3. CUMULATIVE EFFECT ANALYSIS")
        print("-" * 80)
        # Check if parent imbalances are explained by child imbalances
        cumulative_analysis = []
        for entity_name, data in entity_balances.items():
            children = data.get("children", [])
            if children:
                child_balances = [entity_balances.get(c, {}) for c in children if c in entity_balances]
                if child_balances:
                    child_sum = sum(c.get("difference", 0) for c in child_balances)
                    parent_diff = data["difference"]
                    unexplained = parent_diff - child_sum
                    cumulative_analysis.append({
                        "entity": entity_name,
                        "parent_diff": parent_diff,
                        "child_sum": child_sum,
                        "unexplained": unexplained
                    })
        
        if cumulative_analysis:
            print(f"Analyzed {len(cumulative_analysis)} parent entities with unbalanced children")
            print("\nTop 10 entities with largest unexplained imbalances:")
            sorted_cumulative = sorted(cumulative_analysis, key=lambda x: abs(x["unexplained"]), reverse=True)[:10]
            for i, analysis in enumerate(sorted_cumulative, 1):
                print(f"  {i}. {analysis['entity']}:")
                print(f"     Parent imbalance: ${analysis['parent_diff']:,.2f}")
                print(f"     Sum of child imbalances: ${analysis['child_sum']:,.2f}")
                print(f"     Unexplained difference: ${analysis['unexplained']:,.2f}")
        else:
            print("No parent entities with unbalanced children found")
        print()
        
        # Analysis 4: Magnitude Distribution
        print("4. MAGNITUDE DISTRIBUTION")
        print("-" * 80)
        magnitude_ranges = {
            "Very Large (>$10M)": 0,
            "Large ($1M-$10M)": 0,
            "Medium ($100K-$1M)": 0,
            "Small ($10K-$100K)": 0,
            "Very Small (<$10K)": 0
        }
        
        for data in entity_balances.values():
            abs_diff = abs(data["difference"])
            if abs_diff >= 10_000_000:
                magnitude_ranges["Very Large (>$10M)"] += 1
            elif abs_diff >= 1_000_000:
                magnitude_ranges["Large ($1M-$10M)"] += 1
            elif abs_diff >= 100_000:
                magnitude_ranges["Medium ($100K-$1M)"] += 1
            elif abs_diff >= 10_000:
                magnitude_ranges["Small ($10K-$100K)"] += 1
            else:
                magnitude_ranges["Very Small (<$10K)"] += 1
        
        for range_name, count in magnitude_ranges.items():
            if count > 0:
                print(f"  {range_name}: {count} entities")
        print()
        
        # Analysis 5: Entity Characteristics
        print("5. ENTITY CHARACTERISTICS")
        print("-" * 80)
        # Check for patterns in entity names
        segment_entities = defaultdict(list)
        for entity_name, data in entity_balances.items():
            if "Segment" in entity_name:
                segment_entities["Segments"].append((entity_name, data["difference"]))
            elif "Corp" in entity_name or "Corporate" in entity_name:
                segment_entities["Corporate"].append((entity_name, data["difference"]))
            elif "I/C" in entity_name or "Intercompany" in entity_name:
                segment_entities["Intercompany"].append((entity_name, data["difference"]))
            elif "Consolidated" in entity_name:
                segment_entities["Consolidated"].append((entity_name, data["difference"]))
        
        for category, entities in segment_entities.items():
            if entities:
                total = sum(diff for _, diff in entities)
                print(f"  {category}: {len(entities)} entities, Total imbalance: ${total:,.2f}")
        print()
        
        # Analysis 6: Potential Root Causes
        print("6. POTENTIAL ROOT CAUSES")
        print("-" * 80)
        print("Based on the analysis, potential contributing factors include:")
        print()
        
        # Check for intercompany issues
        ic_entities = [e for e in entity_balances.keys() if "I/C" in e or "Intercompany" in e]
        if ic_entities:
            ic_total = sum(entity_balances[e]["difference"] for e in ic_entities)
            print(f"  • Intercompany Elimination Issues:")
            print(f"    - {len(ic_entities)} intercompany entities unbalanced")
            print(f"    - Total intercompany imbalance: ${ic_total:,.2f}")
            print(f"    - Suggests intercompany transactions may not be fully eliminated")
            print()
        
        # Check for consolidation rollup issues
        if cumulative_analysis:
            large_unexplained = [a for a in cumulative_analysis if abs(a["unexplained"]) > 1_000_000]
            if large_unexplained:
                print(f"  • Consolidation Rollup Issues:")
                print(f"    - {len(large_unexplained)} parent entities have large unexplained differences")
                print(f"    - Suggests consolidation adjustments or eliminations may be missing")
                print()
        
        # Check magnitude
        very_large = magnitude_ranges["Very Large (>$10M)"]
        if very_large > 0:
            print(f"  • Significant Data Quality Issues:")
            print(f"    - {very_large} entities with imbalances >$10M")
            print(f"    - Suggests potential data entry errors or missing journal entries")
            print()
        
        # Check direction
        if len(positive_imbalances) != len(negative_imbalances):
            print(f"  • Systematic Bias:")
            print(f"    - {len(positive_imbalances)} entities with positive imbalances")
            print(f"    - {len(negative_imbalances)} entities with negative imbalances")
            print(f"    - Asymmetric distribution suggests systematic accounting issue")
            print()
        
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print()
        print("1. Review intercompany transactions and eliminations")
        print("2. Verify consolidation adjustments are properly applied")
        print("3. Check for missing journal entries in entities with large imbalances")
        print("4. Validate account mappings and formulas")
        print("5. Review currency translation adjustments")
        print("6. Verify period-end closing procedures were completed")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(analyze_imbalance_causes())

