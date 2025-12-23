"""Get CTA (Cumulative Translation Adjustment) for FY25 by entity and highlight largest FX impacts."""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve, export_data_slice


async def get_cta_by_entity_fy25():
    """Get CTA for FY25 by entity and highlight entities with largest FX impact."""
    print("=" * 80)
    print("CUMULATIVE TRANSLATION ADJUSTMENT (CTA) BY ENTITY - FY25")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Key entities to check - focusing on major segments and consolidated entities
        key_entities = [
            "FCCS_Total Geography",
            "Industrial Segment",
            "Energy Segment",
            "Fire Protection Segment",
            "Administrative Segment",
            "Industrial Consolidated Corp",
            "Energy Consolidated Corp",
            "Phoenix - Consolidated",
            "Washington Consolidated",
            "Leland Consolidated",
            "IFS Consolidated",
            "Carlsbad Consolidated Branch",
            "Williston Consolidated Branch",
            "Monumental Rollup",
            "Total Monumental",
            "Total MSC",
        ]
        
        print(f"Retrieving CTA data for {len(key_entities)} key entities...")
        print()
        
        cta_results = []
        
        # First, try using export_data_slice to get multiple entities at once
        print("Attempting bulk retrieval using export_data_slice...")
        try:
            grid_definition = {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        ["FY25"], ["Actual"], ["FCCS_YTD"], ["FCCS_Entity Total"],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], ["FCCS_Total Geography"], ["Entity Currency"],
                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": [{"members": [["Dec"]]}],
                "rows": [
                    {"members": [[entity] for entity in key_entities]},
                    {"members": [["FCCS_CTA"]]}
                ]
            }
            
            slice_result = await export_data_slice(grid_definition, "Consol")
            
            if slice_result.get("status") == "success":
                data = slice_result.get("data", {})
                rows = data.get("rows", [])
                
                if rows:
                    # Parse the results - rows should contain entity data
                    for i, row in enumerate(rows):
                        if i < len(key_entities) and row.get("data"):
                            entity = key_entities[i]
                            value = row["data"][0] if row["data"] else None
                            
                            if value is not None:
                                try:
                                    value_float = float(value)
                                    cta_results.append({
                                        "entity": entity,
                                        "cta": value_float
                                    })
                                    print(f"  [OK] {entity:40s}: ${value_float:>15,.2f}")
                                except (ValueError, TypeError):
                                    print(f"  [ERR] {entity:40s}: Invalid value")
                            else:
                                print(f"  [-] {entity:40s}: No data")
                    print()
                    print("Bulk retrieval completed.")
        except Exception as e:
            print(f"Bulk retrieval failed: {str(e)}")
            print("Falling back to individual entity queries...")
            print()
        
        # If bulk retrieval didn't work or didn't return all data, query individually
        if len(cta_results) < len(key_entities):
            print("Querying remaining entities individually...")
            print()
            
            # Only query entities we don't have data for
            entities_to_query = [e for e in key_entities if not any(r["entity"] == e for r in cta_results)]
            
            for entity in entities_to_query:
                try:
                    result = await smart_retrieve(
                        account="FCCS_CTA",
                        entity=entity,
                        period="Dec",  # Year-to-date cumulative
                        years="FY25",
                        scenario="Actual"
                    )
                
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        rows = data.get("rows", [])
                        
                        value = None
                        if rows and rows[0].get("data"):
                            value = rows[0]["data"][0]
                        
                        if value is not None:
                            try:
                                value_float = float(value)
                                cta_results.append({
                                    "entity": entity,
                                    "cta": value_float
                                })
                                print(f"  [OK] {entity:40s}: ${value_float:>15,.2f}")
                            except (ValueError, TypeError):
                                print(f"  [ERR] {entity:40s}: Invalid value ({value})")
                        else:
                            print(f"  [-] {entity:40s}: No data")
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"  [ERR] {entity:40s}: Error - {error}")
                        
                except Exception as e:
                    print(f"  [ERR] {entity:40s}: Exception - {str(e)}")
        
        print()
        print("=" * 80)
        
        if cta_results:
            # Sort by absolute value to find largest impacts
            cta_results_sorted = sorted(
                cta_results, 
                key=lambda x: abs(x["cta"]), 
                reverse=True
            )
            
            print("\n*** CTA SUMMARY - FY25 (Year-to-Date through Dec) ***")
            print("-" * 80)
            print(f"{'Rank':<6} {'Entity':<45} {'CTA Amount':>20}")
            print("-" * 80)
            
            for idx, result in enumerate(cta_results_sorted, 1):
                entity = result["entity"]
                cta = result["cta"]
                
                # Highlight top 5 largest impacts
                highlight = "***" if idx <= 5 else "   "
                
                print(f"{highlight} {idx:<4} {entity:<45} ${cta:>18,.2f}")
            
            print("-" * 80)
            print(f"{'Total Entities with CTA':<52} {len(cta_results):>20}")
            
            # Calculate totals
            total_cta = sum(r["cta"] for r in cta_results)
            positive_cta = sum(r["cta"] for r in cta_results if r["cta"] > 0)
            negative_cta = sum(r["cta"] for r in cta_results if r["cta"] < 0)
            
            print(f"{'Sum of All CTA Values':<52} ${total_cta:>18,.2f}")
            print(f"{'Sum of Positive CTA':<52} ${positive_cta:>18,.2f}")
            print(f"{'Sum of Negative CTA':<52} ${negative_cta:>18,.2f}")
            
            print()
            print("=" * 80)
            print("\n*** TOP 5 ENTITIES WITH LARGEST FX IMPACT (by absolute value): ***")
            print("-" * 80)
            
            for idx, result in enumerate(cta_results_sorted[:5], 1):
                entity = result["entity"]
                cta = result["cta"]
                impact_type = "GAIN" if cta > 0 else "LOSS"
                
                print(f"\n{idx}. {entity}")
                print(f"   CTA: ${cta:,.2f} ({impact_type})")
                print(f"   Impact: ${abs(cta):,.2f} in {'favorable' if cta > 0 else 'unfavorable'} FX translation")
            
            print()
            print("=" * 80)
            
            # Additional analysis
            print("\n*** ADDITIONAL INSIGHTS: ***")
            print("-" * 80)
            
            entities_with_gains = [r for r in cta_results if r["cta"] > 0]
            entities_with_losses = [r for r in cta_results if r["cta"] < 0]
            entities_with_zero = [r for r in cta_results if r["cta"] == 0]
            
            print(f"Entities with FX gains (positive CTA): {len(entities_with_gains)}")
            print(f"Entities with FX losses (negative CTA): {len(entities_with_losses)}")
            if entities_with_zero:
                print(f"Entities with zero CTA: {len(entities_with_zero)}")
            
            if entities_with_gains:
                largest_gain = max(entities_with_gains, key=lambda x: x["cta"])
                print(f"\nLargest FX Gain: {largest_gain['entity']} (${largest_gain['cta']:,.2f})")
            
            if entities_with_losses:
                largest_loss = min(entities_with_losses, key=lambda x: x["cta"])
                print(f"Largest FX Loss: {largest_loss['entity']} (${largest_loss['cta']:,.2f})")
            
        else:
            print("\n*** WARNING: No CTA data found for FY25 ***")
            print("\nPossible reasons:")
            print("  - Data has not been loaded for FY25")
            print("  - Translation adjustments have not been calculated")
            print("  - Consolidation has not been run for FY25")
            print("  - Entities may not have foreign currency exposure")
            print("\nRecommendation: Verify that:")
            print("  1. Data has been loaded for FY25")
            print("  2. Consolidation business rule has been executed")
            print("  3. Exchange rates have been set up correctly")
        
        print()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await close_agent()


if __name__ == "__main__":
    asyncio.run(get_cta_by_entity_fy25())

