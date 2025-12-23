"""
Consolidation Process Overview Report.

This report shows the step-by-step process of consolidation for a specific entity.
It tracks how data flows from Local GAAP (Entity Input) to the final Consolidated numbers (Contribution).
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import export_data_slice
from fccs_agent.client.fccs_client import FccsClient

async def get_consolidation_data(
    entity: str,
    account: str,
    period: str,
    year: str,
    scenario: str = "Actual"
) -> Dict[str, float]:
    """Retrieve data for different consolidation stages."""
    stages = {
        "Entity Input": "FCCS_Entity Input",
        "Entity Total": "FCCS_Entity Total",
        "Proportion": "FCCS_Proportion",
        "Elimination": "FCCS_Elimination",
        "Contribution": "FCCS_Contribution"
    }
    
    results = {}
    
    # We need to import the global variables from agent.py
    # Since they are not exported, we use initialize_agent and then access them via the tool functions
    # or we can use the client directly if we have access to it.
    
    from fccs_agent.agent import _fccs_client, _app_name
    
    for stage_name, consol_member in stages.items():
        try:
            # POV order based on smart_retrieve in fccs_agent/tools/data.py
            # 13 dimensions in POV: Years, Scenario, View, Consolidation, ICP, Data Source, Movement, Entity, Currency, 4 Customs
            grid_definition = {
                "suppressMissingBlocks": True,
                "pov": {
                    "members": [
                        [year], [scenario], ["FCCS_YTD"], [consol_member],
                        ["FCCS_Intercompany Top"], ["FCCS_Total Data Source"],
                        ["FCCS_Mvmts_Total"], [entity], ["Entity Currency"],
                        ["Total Custom 3"], ["Total Region"], ["Total Venturi Entity"],
                        ["Total Custom 4"]
                    ]
                },
                "columns": [{"members": [[period]]}],
                "rows": [{"members": [[account]]}]
            }
            
            res = await _fccs_client.export_data_slice(_app_name, "Consol", grid_definition)
            
            value = 0.0
            if res and "rows" in res and res["rows"]:
                data_row = res["rows"][0].get("data")
                if data_row and data_row[0] is not None:
                    value = float(data_row[0])
            
            # Special handling for Mock Mode to make the report look better
            if os.environ.get("FCCS_MOCK_MODE", "false").lower() == "true":
                base = 1000.0 if account == "FCCS_Net Income" else 5000.0
                mock_values = {
                    "FCCS_Entity Input": base,
                    "FCCS_Entity Total": base * 1.05,
                    "FCCS_Proportion": base * 1.05,
                    "FCCS_Elimination": -base * 0.2,
                    "FCCS_Contribution": base * 1.05 - base * 0.2
                }
                value = mock_values.get(consol_member, value)
            
            results[stage_name] = value
            print(f"[OK] {stage_name} ({consol_member}): ${value:,.2f}")
            
        except Exception as e:
            # If in mock mode or error, generate some semi-realistic mock data if needed
            if os.environ.get("FCCS_MOCK_MODE", "false").lower() == "true":
                # Create a flow: 1000 -> 1050 -> 1050 -> -200 -> 850
                base = 1000.0 if account == "FCCS_Net Income" else 5000.0
                mock_values = {
                    "Entity Input": base,
                    "Entity Total": base * 1.05,
                    "Proportion": base * 1.05,
                    "Elimination": -base * 0.2,
                    "Contribution": base * 1.05 - base * 0.2
                }
                results[stage_name] = mock_values.get(stage_name, 0.0)
                print(f"[MOCK] {stage_name} ({consol_member}): ${results[stage_name]:,.2f}")
            else:
                print(f"[ERROR] Failed to fetch {stage_name}: {e}")
                results[stage_name] = 0.0
            
    return results

def generate_html_report(
    entity: str,
    account: str,
    period: str,
    year: str,
    scenario: str,
    data: Dict[str, float]
) -> str:
    """Generate HTML report with a consolidation flow visualization."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"consolidation_overview_{entity}_{timestamp}.html"
    
    # Calculate variances/adjustments
    local_adj = data["Entity Total"] - data["Entity Input"]
    prop_adj = data["Proportion"] - data["Entity Total"]
    elim = data["Elimination"]
    
    local_adj_class = "negative" if local_adj < 0 else ""
    prop_adj_class = "negative" if prop_adj < 0 else ""
    elim_class = "negative" if elim < 0 else ""
    
    local_adj_sign = "+" if local_adj >= 0 else ""
    prop_adj_sign = "+" if prop_adj >= 0 else ""
    elim_sign = "+" if elim >= 0 else ""
    
    local_adj_color = "#dc3545" if local_adj < 0 else "#28a745"
    elim_color = "#dc3545" if elim < 0 else "#28a745"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Consolidation Process Overview - {entity}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f0f2f5; color: #333; }}
        .container {{ max-width: 1000px; margin: auto; background-color: white; padding: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 8px; }}
        h1 {{ color: #1a3a6c; border-bottom: 3px solid #1a3a6c; padding-bottom: 10px; margin-bottom: 20px; }}
        .metadata {{ display: flex; justify-content: space-between; margin-bottom: 30px; background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 5px solid #1a3a6c; }}
        .metadata-item {{ font-size: 14px; }}
        .metadata-label {{ font-weight: bold; color: #666; text-transform: uppercase; font-size: 11px; display: block; }}
        
        /* Flow Visualization */
        .flow-container {{ display: flex; align-items: center; justify-content: space-between; margin: 50px 0; padding: 20px; background: #fff; overflow-x: auto; }}
        .flow-step {{ text-align: center; flex: 1; min-width: 150px; position: relative; }}
        .step-box {{ background: #1a3a6c; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        .step-value {{ font-size: 18px; font-weight: bold; }}
        .step-name {{ font-size: 12px; text-transform: uppercase; margin-top: 5px; opacity: 0.9; }}
        .flow-arrow {{ font-size: 24px; color: #1a3a6c; padding: 0 10px; }}
        .flow-adj {{ font-size: 11px; color: #28a745; font-weight: bold; margin-bottom: 5px; }}
        .flow-adj.negative {{ color: #dc3545; }}
        
        /* Table Styles */
        table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
        th {{ background-color: #1a3a6c; color: white; padding: 12px; text-align: left; font-size: 14px; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
        tr:hover {{ background-color: #f8f9fa; }}
        .val {{ text-align: right; font-family: 'Courier New', Courier, monospace; font-weight: bold; }}
        .total-row {{ background-color: #e9ecef; font-weight: bold; }}
        
        .footer {{ margin-top: 50px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
        .tag {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; margin-left: 5px; }}
        .tag-input {{ background: #e3f2fd; color: #0d47a1; }}
        .tag-total {{ background: #e8f5e9; color: #1b5e20; }}
        .tag-elim {{ background: #fff3e0; color: #e65100; }}
        .tag-contrib {{ background: #f3e5f5; color: #4a148c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Consolidation Process Overview</h1>
        
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Entity</span>
                {entity}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Account</span>
                {account}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Period / Year</span>
                {period} {year}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Scenario</span>
                {scenario}
            </div>
        </div>

        <h3>Consolidation Flow</h3>
        <div class="flow-container">
            <div class="flow-step">
                <div class="step-box">
                    <div class="step-value">${data['Entity Input']:,.0f}</div>
                    <div class="step-name">Local GAAP</div>
                </div>
                <div class="flow-adj {local_adj_class}">{local_adj_sign}{local_adj:,.0f} Adj.</div>
            </div>
            
            <div class="flow-arrow">→</div>
            
            <div class="flow-step">
                <div class="step-box" style="background: #2c5aa0;">
                    <div class="step-value">${data['Entity Total']:,.0f}</div>
                    <div class="step-name">Entity Total</div>
                </div>
                <div class="flow-adj {prop_adj_class}">{prop_adj_sign}{prop_adj:,.0f} Prop.</div>
            </div>
            
            <div class="flow-arrow">→</div>
            
            <div class="flow-step">
                <div class="step-box" style="background: #4a90e2;">
                    <div class="step-value">${data['Proportion']:,.0f}</div>
                    <div class="step-name">Proportion</div>
                </div>
                <div class="flow-adj {elim_class}">{elim_sign}{elim:,.0f} Elim.</div>
            </div>
            
            <div class="flow-arrow">→</div>
            
            <div class="flow-step">
                <div class="step-box" style="background: #00bcd4;">
                    <div class="step-value">${data['Contribution']:,.0f}</div>
                    <div class="step-name">Contribution</div>
                </div>
            </div>
        </div>

        <h3>Detailed Process Steps</h3>
        <table>
            <thead>
                <tr>
                    <th>Consolidation Step</th>
                    <th>Member</th>
                    <th class="val">Value ($)</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Local Data Entry <span class="tag tag-input">STEP 1</span></td>
                    <td>FCCS_Entity Input</td>
                    <td class="val">${data['Entity Input']:,.2f}</td>
                    <td>Original data as loaded from the local ERP/Source.</td>
                </tr>
                <tr>
                    <td>Local Adjustments</td>
                    <td>-</td>
                    <td class="val" style="color: {local_adj_color};">{local_adj:,.2f}</td>
                    <td>Manual journals and automated local adjustments.</td>
                </tr>
                <tr class="total-row">
                    <td>Entity Total <span class="tag tag-total">STEP 2</span></td>
                    <td>FCCS_Entity Total</td>
                    <td class="val">${data['Entity Total']:,.2f}</td>
                    <td>Total value for the entity before any group-level processing.</td>
                </tr>
                <tr>
                    <td>Proportional Consolidation</td>
                    <td>FCCS_Proportion</td>
                    <td class="val">${data['Proportion']:,.2f}</td>
                    <td>Entity total multiplied by consolidation percentage.</td>
                </tr>
                <tr>
                    <td>Intercompany Eliminations <span class="tag tag-elim">STEP 3</span></td>
                    <td>FCCS_Elimination</td>
                    <td class="val" style="color: {elim_color};">{elim:,.2f}</td>
                    <td>Elimination of intercompany balances at the first common parent.</td>
                </tr>
                <tr class="total-row">
                    <td>Contribution to Parent <span class="tag tag-contrib">STEP 4</span></td>
                    <td>FCCS_Contribution</td>
                    <td class="val">${data['Contribution']:,.2f}</td>
                    <td>The final amount this entity contributes to its parent's consolidated total.</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <p><strong>Oracle EPM FCCS Consolidation Report</strong></p>
            <p>Generated by Aliki FCCS Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save file
    filepath = Path(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(filepath.absolute())

async def main():
    """Main execution function."""
    print("=" * 80)
    print("FCCS CONSOLIDATION PROCESS OVERVIEW")
    print("=" * 80)
    
    # Configuration
    entity = os.environ.get("REPORT_ENTITY", "FCCS_Total Geography")
    account = os.environ.get("REPORT_ACCOUNT", "FCCS_Net Income")
    period = os.environ.get("REPORT_PERIOD", "Dec")
    year = os.environ.get("REPORT_YEAR", "FY25")
    scenario = os.environ.get("REPORT_SCENARIO", "Actual")
    
    try:
        config = load_config()
        await initialize_agent(config)
        print(f"[OK] Agent initialized for {entity}")
        
        # Collect data
        print(f"Collecting consolidation stages for {account}...")
        data = await get_consolidation_data(entity, account, period, year, scenario)
        
        # Generate report
        print("\nGenerating HTML report...")
        report_path = generate_html_report(entity, account, period, year, scenario, data)
        
        print("\n" + "=" * 80)
        print(f"SUCCESS: Consolidation Overview generated!")
        print(f"Report path: {report_path}")
        print("=" * 80)
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

