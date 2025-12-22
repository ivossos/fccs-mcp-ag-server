import asyncio
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent, execute_tool

# List of L0 Movements extracted from metadata
L0_MOVEMENTS = [
    "FCCS_No Movement", "FCCS_OpeningBalance", "FCCS_OpeningBalanceAdjustment", 
    "FCCS_Mvmts_Cash", "FCCS_Mvmts_NetIncome", "Mvmts_Non-Cash Interest Expense", 
    "Mvmts_Non-Cash(Gain)/Loss", "Mvmts_Cash(Gain)/Loss", "Mvmts_Intercompany", 
    "FCCS_Mvmts_DepreciationAndAmortization", "Mvmts_Depreciation", "Mvmts_Amortization", 
    "FCCS_Mvmts_AccountsReceivable", "FCCS_Mvmts_Inventories", "FCCS_Mvmts_OtherCurrentAssets", 
    "FCCS_Mvmts_AccountsPayable", "FCCS_Mvmts_OtherCurrentLiabilities", "Mvmts_OtherAssets", 
    "Mvmts_OtherLiabilities", "Mvmts_Prepaid Assets", "Mvmts_Operating Lease ROU Assets", 
    "Mvmts_Finance Lease ROU Assets", "Mvmts_Accrued Expenses", "Mvmts_Operating Lease Liabilities", 
    "FCCS_Mvmts_CapitalExpenditures", "FCCS_Mvmts_ProceedsFromSalesOfPPE", 
    "FCCS_Mvmts_OtherInvestingActivities", "Mvmts_Asset Disposals", 
    "Mvmts_Other Fixed Asset Changes", "Mvmts_Goodwill", "Mvmts_Intangible Assets", 
    "FCCS_Mvmts_IssueOfStock", "FCCS_Mvmts_ProceedsFromDebt", "FCCS_Mvmts_RepaymentOfDebt", 
    "FCCS_Mvmts_OtherFinancingActivities", "Mvmts_Revolver Draw / (Paydown)", 
    "Mvmts_Term Loan Draw / (Paydown)", "Mvmts_Debt Issuance Costs", 
    "Mvmts_Other Debt Draw / (Paydown)", "Mvmts_Finance Lease Liabilities", 
    "Mvmts_Contingent Consideration", "Mvmts_Equity Proceeds / (Distributions)"
]

async def generate_l0_movements_report():
    print("=" * 70)
    print("FCCS L0 Movements Data Report")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        
        results = []
        print(f"Retrieving data for {len(L0_MOVEMENTS)} Level 0 movements...")
        
        # We'll use a specific intersection for the report
        entity = "FCCS_Total Geography"
        account = "FCCS_Net Income" # Net Income is a good anchor, though some movements might be 0 for it
        # Alternatively, use a generic account if needed, but let's stick to Net Income for now
        
        for movement in L0_MOVEMENTS:
            try:
                # Use the new tool we created!
                res = await execute_tool("smart_retrieve_with_movement", {
                    "account": account,
                    "movement": movement,
                    "entity": entity,
                    "period": "Jan",
                    "years": "FY24",
                    "scenario": "Actual"
                })
                
                if res.get("status") == "success":
                    data = res.get("data", {})
                    rows = data.get("rows", [])
                    if rows and rows[0].get("data"):
                        value = rows[0]["data"][0]
                        if value is not None and value != 0:
                            results.append({
                                "Movement": movement,
                                "Value": float(value)
                            })
                            print(f"  [DATA] {movement}: {value}")
                        else:
                            # Still include zero/none for the full list if desired, or skip
                            pass
            except Exception as e:
                # Skip errors for specific movements
                pass
        
        if results:
            # Create a simple HTML report
            df = pd.DataFrame(results)
            report_filename = f"L0_Movements_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: sans-serif; margin: 40px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .header {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>FCCS Level 0 Movements Report</h1>
                    <p><strong>Entity:</strong> {entity}</p>
                    <p><strong>Account:</strong> {account}</p>
                    <p><strong>Period/Year:</strong> Jan FY24 (Actual)</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                {df.to_html(index=False, classes='table')}
            </body>
            </html>
            """
            
            with open(report_filename, "w") as f:
                f.write(html_content)
                
            print(f"\n[SUCCESS] Report generated: {report_filename}")
        else:
            print("\n[INFO] No non-zero data found for the specified intersection across L0 movements.")
            
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(generate_l0_movements_report())

