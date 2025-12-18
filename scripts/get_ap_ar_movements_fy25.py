"""Get AP and AR balances for FCCS_US FY25 YTD and show top 5 largest movements - HTML Report."""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve


async def get_period_balance(account: str, entity: str, period: str, year: str) -> float:
    """Get balance for a specific period."""
    try:
        result = await smart_retrieve(
            account=account,
            entity=entity,
            period=period,
            years=year,
            scenario="Actual"
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else 0.0
    except Exception as e:
        print(f"  [WARNING] Error retrieving {account} for {period}: {str(e)[:100]}")
    return 0.0


def generate_html_report(
    entity: str,
    year: str,
    ap_balances: Dict[str, float],
    ar_balances: Dict[str, float],
    all_movements: List[Dict],
    top_5: List[Dict]
) -> str:
    """Generate HTML report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Calculate totals
    ap_ytd = ap_balances.get("Dec", 0.0)
    ar_ytd = ar_balances.get("Dec", 0.0)
    ap_movements = [m for m in all_movements if m["account_type"] == "AP"]
    ar_movements = [m for m in all_movements if m["account_type"] == "AR"]
    ap_total_movement = sum(m["movement"] for m in ap_movements)
    ar_total_movement = sum(m["movement"] for m in ar_movements)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AP & AR Balances Report - {entity} {year}</title>
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
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .card.ap {{
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        }}
        .card.ar {{
            background: linear-gradient(135deg, #a8e6cf 0%, #88d8a3 100%);
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background: #f5f7fa;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .top-movement {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .period-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }}
        .period-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            border: 2px solid #e0e0e0;
        }}
        .period-item .period {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .period-item .value {{
            font-size: 0.9em;
            color: #333;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AP & AR Balances Report</h1>
            <p>{entity} - {year} YTD Analysis</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime("%B %d, %Y %I:%M %p")}</p>
        </div>
        
        <div class="content">
            <div class="summary-cards">
                <div class="card ap">
                    <h3>Accounts Payable (YTD)</h3>
                    <div class="value">${ap_ytd:,.2f}</div>
                </div>
                <div class="card ar">
                    <h3>Accounts Receivable (YTD)</h3>
                    <div class="value">${ar_ytd:,.2f}</div>
                </div>
                <div class="card">
                    <h3>AP Total Movement</h3>
                    <div class="value {'positive' if ap_total_movement >= 0 else 'negative'}">${ap_total_movement:,.2f}</div>
                </div>
                <div class="card">
                    <h3>AR Total Movement</h3>
                    <div class="value {'positive' if ar_total_movement >= 0 else 'negative'}">${ar_total_movement:,.2f}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Top 5 Largest Movements</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Account</th>
                            <th>From Period</th>
                            <th>To Period</th>
                            <th>From Balance</th>
                            <th>To Balance</th>
                            <th>Movement</th>
                            <th>% Change</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for i, movement in enumerate(top_5, 1):
        movement_class = "positive" if movement["movement"] >= 0 else "negative"
        row_class = "top-movement" if i == 1 else ""
        html += f"""
                        <tr class="{row_class}">
                            <td><strong>#{i}</strong></td>
                            <td>{movement['account_type']}<br><small>{movement['account_name']}</small></td>
                            <td>{movement['from_period']}</td>
                            <td>{movement['to_period']}</td>
                            <td>${movement['from_balance']:,.2f}</td>
                            <td>${movement['to_balance']:,.2f}</td>
                            <td class="{movement_class}">${movement['movement']:,.2f}</td>
                            <td class="{movement_class}">{movement['movement_pct']:+.2f}%</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Monthly Balances - Accounts Payable</h2>
                <div class="period-grid">
"""
    
    for period in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        balance = ap_balances.get(period, 0.0)
        html += f"""
                    <div class="period-item">
                        <div class="period">{period}</div>
                        <div class="value">${balance:,.2f}</div>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2>Monthly Balances - Accounts Receivable</h2>
                <div class="period-grid">
"""
    
    for period in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        balance = ar_balances.get(period, 0.0)
        html += f"""
                    <div class="period-item">
                        <div class="period">{period}</div>
                        <div class="value">${balance:,.2f}</div>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <div class="section">
                <h2>All Movements</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Account</th>
                            <th>From Period</th>
                            <th>To Period</th>
                            <th>From Balance</th>
                            <th>To Balance</th>
                            <th>Movement</th>
                            <th>% Change</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for movement in sorted(all_movements, key=lambda x: abs(x["movement"]), reverse=True):
        movement_class = "positive" if movement["movement"] >= 0 else "negative"
        html += f"""
                        <tr>
                            <td>{movement['account_type']}</td>
                            <td>{movement['from_period']}</td>
                            <td>{movement['to_period']}</td>
                            <td>${movement['from_balance']:,.2f}</td>
                            <td>${movement['to_balance']:,.2f}</td>
                            <td class="{movement_class}">${movement['movement']:,.2f}</td>
                            <td class="{movement_class}">{movement['movement_pct']:+.2f}%</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>FCCS Financial Reporting System | Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


async def get_ap_ar_movements():
    """Get AP and AR balances for FCCS_US FY25 YTD and calculate movements."""
    print("=" * 80)
    print("AP & AR BALANCES - FCCS_US FY25 YTD - HTML REPORT GENERATION")
    print("=" * 80)
    print()
    
    entity = "FCCS_US"
    year = "FY25"
    periods = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    accounts = {
        "AP": "FCCS_Acct Payable",
        "AR": "FCCS_Acct Receivable"
    }
    
    try:
        config = load_config()
        await initialize_agent(config)
        print(f"[OK] Connected to FCCS")
        print()
        
        # Retrieve data for both accounts across all periods
        all_movements = []
        ap_balances = {}
        ar_balances = {}
        
        for account_type, account_name in accounts.items():
            print(f"Retrieving {account_type} ({account_name}) balances...")
            balances = {}
            
            for period in periods:
                balance = await get_period_balance(account_name, entity, period, year)
                balances[period] = balance
                print(f"  {period}: ${balance:,.2f}")
            
            if account_type == "AP":
                ap_balances = balances
            else:
                ar_balances = balances
            
            print()
            
            # Calculate period-over-period movements
            print(f"Calculating {account_type} movements...")
            prev_balance = None
            prev_period = None
            
            for period in periods:
                current_balance = balances[period]
                
                if prev_balance is not None:
                    movement = current_balance - prev_balance
                    movement_pct = (movement / abs(prev_balance) * 100) if prev_balance != 0 else 0
                    
                    all_movements.append({
                        "account_type": account_type,
                        "account_name": account_name,
                        "from_period": prev_period,
                        "to_period": period,
                        "from_balance": prev_balance,
                        "to_balance": current_balance,
                        "movement": movement,
                        "movement_pct": movement_pct
                    })
                    
                    print(f"  {prev_period} -> {period}: ${movement:,.2f} ({movement_pct:+.2f}%)")
                
                prev_balance = current_balance
                prev_period = period
            
            print()
        
        # Sort by absolute movement and get top 5
        all_movements.sort(key=lambda x: abs(x["movement"]), reverse=True)
        top_5 = all_movements[:5]
        
        print("Generating HTML report...")
        
        # Generate HTML report
        html_content = generate_html_report(
            entity=entity,
            year=year,
            ap_balances=ap_balances,
            ar_balances=ar_balances,
            all_movements=all_movements,
            top_5=top_5
        )
        
        # Save HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"AP_AR_Movements_Report_{entity}_{year}_{timestamp}.html"
        filepath = Path(__file__).parent.parent / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n[SUCCESS] HTML report generated: {filename}")
        print(f"Location: {filepath}")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(get_ap_ar_movements())
