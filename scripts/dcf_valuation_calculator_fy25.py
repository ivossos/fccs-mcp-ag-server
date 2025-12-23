"""
Discounted Cash Flow (DCF) Valuation Calculator - FY25 Base Year
Based on FCCS financial data for VENT
"""

import pandas as pd
import numpy as np
from datetime import datetime

class DCFValuationFY25:
    def __init__(self):
        # Base Year (FY25) Financial Data from FCCS
        self.base_revenue = 403932211.85
        self.base_ebitda = 23107298.11
        self.base_operating_income = 23520859.01
        self.base_net_income = -6285631.23
        self.cash = 767034.25
        self.capex = 1179592.57
        
        # Assumptions
        self.revenue_growth_y1_3 = 0.05  # 5% for years 1-3
        self.revenue_growth_y4_5 = 0.03  # 3% for years 4-5
        self.terminal_growth = 0.025     # 2.5% terminal growth
        self.ebitda_margin = self.base_ebitda / self.base_revenue  # ~5.72%
        self.capex_pct_y1_3 = 0.003      # 0.3% of revenue (based on FY25 ratio)
        self.capex_pct_y4_5 = 0.003      # 0.3% of revenue
        self.tax_rate = 0.25              # 25% tax rate
        self.wacc = 0.10                  # 10% WACC
        
    def calculate_fcf(self, ebitda, capex, tax_rate):
        """Calculate Free Cash Flow from EBITDA"""
        # FCF = EBITDA * (1 - tax_rate) - CapEx
        return ebitda * (1 - tax_rate) - capex
    
    def project_cash_flows(self, years=5):
        """Project cash flows for specified number of years"""
        projections = []
        current_revenue = self.base_revenue
        
        for year in range(1, years + 1):
            # Determine growth rate
            if year <= 3:
                growth_rate = self.revenue_growth_y1_3
                capex_pct = self.capex_pct_y1_3
            else:
                growth_rate = self.revenue_growth_y4_5
                capex_pct = self.capex_pct_y4_5
            
            # Project revenue
            current_revenue = current_revenue * (1 + growth_rate)
            
            # Project EBITDA
            ebitda = current_revenue * self.ebitda_margin
            
            # Project CapEx
            capex = current_revenue * capex_pct
            
            # Calculate FCF
            fcf = self.calculate_fcf(ebitda, capex, self.tax_rate)
            
            # Calculate Present Value
            pv_fcf = fcf / ((1 + self.wacc) ** year)
            
            projections.append({
                'Year': f'FY{25 + year}',
                'Revenue': current_revenue,
                'EBITDA': ebitda,
                'EBITDA_Margin': self.ebitda_margin,
                'CapEx': capex,
                'FCF': fcf,
                'PV_FCF': pv_fcf
            })
        
        return projections
    
    def calculate_terminal_value(self, final_fcf, terminal_growth, wacc):
        """Calculate terminal value using Gordon Growth Model"""
        terminal_value = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
        return terminal_value
    
    def calculate_enterprise_value(self):
        """Calculate Enterprise Value using DCF method"""
        # Project cash flows
        projections = self.project_cash_flows(years=5)
        
        # Sum of PV of projected FCFs
        pv_projected_fcfs = sum([p['PV_FCF'] for p in projections])
        
        # Terminal value calculation
        final_fcf = projections[-1]['FCF']
        terminal_value = self.calculate_terminal_value(
            final_fcf, 
            self.terminal_growth, 
            self.wacc
        )
        
        # PV of terminal value (discounted back 5 years)
        pv_terminal_value = terminal_value / ((1 + self.wacc) ** 5)
        
        # Enterprise Value
        enterprise_value = pv_projected_fcfs + pv_terminal_value
        
        return {
            'pv_projected_fcfs': pv_projected_fcfs,
            'terminal_value': terminal_value,
            'pv_terminal_value': pv_terminal_value,
            'enterprise_value': enterprise_value,
            'projections': projections
        }
    
    def calculate_equity_value(self, enterprise_value, net_debt=0):
        """Calculate Equity Value from Enterprise Value"""
        equity_value = enterprise_value - net_debt + self.cash
        return equity_value
    
    def sensitivity_analysis(self, wacc_range=None, growth_range=None):
        """Perform sensitivity analysis on key assumptions"""
        if wacc_range is None:
            wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
        if growth_range is None:
            growth_range = [0.015, 0.020, 0.025, 0.030, 0.035]
        
        results = []
        
        for wacc in wacc_range:
            original_wacc = self.wacc
            self.wacc = wacc
            
            for growth in growth_range:
                original_growth = self.terminal_growth
                self.terminal_growth = growth
                
                ev_calc = self.calculate_enterprise_value()
                equity_value = self.calculate_equity_value(ev_calc['enterprise_value'])
                
                results.append({
                    'WACC': f"{wacc*100:.1f}%",
                    'Terminal_Growth': f"{growth*100:.2f}%",
                    'Enterprise_Value': ev_calc['enterprise_value'],
                    'Equity_Value': equity_value
                })
                
                self.terminal_growth = original_growth
            
            self.wacc = original_wacc
        
        return pd.DataFrame(results)
    
    def generate_report(self):
        """Generate comprehensive DCF valuation report"""
        print("=" * 80)
        print("DISCOUNTED CASH FLOW (DCF) VALUATION REPORT - FY25 BASE YEAR")
        print("Company: VENT (Venturi Supply)")
        print(f"Valuation Date: {datetime.now().strftime('%B %d, %Y')}")
        print("=" * 80)
        
        print("\n1. BASE YEAR FINANCIAL METRICS (FY25)")
        print("-" * 80)
        print(f"Revenue:                    ${self.base_revenue:>20,.2f}")
        print(f"EBITDA:                    ${self.base_ebitda:>20,.2f}")
        print(f"EBITDA Margin:              {self.ebitda_margin*100:>19.2f}%")
        print(f"Operating Income:           ${self.base_operating_income:>20,.2f}")
        print(f"Net Income:                 ${self.base_net_income:>20,.2f}")
        print(f"Cash & Equivalents:         ${self.cash:>20,.2f}")
        print(f"Capital Expenditures:       ${self.capex:>20,.2f}")
        
        print("\n2. VALUATION ASSUMPTIONS")
        print("-" * 80)
        print(f"Revenue Growth (Y1-3):      {self.revenue_growth_y1_3*100:>19.2f}%")
        print(f"Revenue Growth (Y4-5):      {self.revenue_growth_y4_5*100:>19.2f}%")
        print(f"Terminal Growth Rate:       {self.terminal_growth*100:>19.2f}%")
        print(f"WACC (Discount Rate):       {self.wacc*100:>19.2f}%")
        print(f"Tax Rate:                   {self.tax_rate*100:>19.2f}%")
        
        print("\n3. 5-YEAR CASH FLOW PROJECTIONS")
        print("-" * 80)
        ev_calc = self.calculate_enterprise_value()
        projections = ev_calc['projections']
        
        df = pd.DataFrame(projections)
        df['Revenue'] = df['Revenue'].apply(lambda x: f"${x:,.2f}")
        df['EBITDA'] = df['EBITDA'].apply(lambda x: f"${x:,.2f}")
        df['CapEx'] = df['CapEx'].apply(lambda x: f"${x:,.2f}")
        df['FCF'] = df['FCF'].apply(lambda x: f"${x:,.2f}")
        df['PV_FCF'] = df['PV_FCF'].apply(lambda x: f"${x:,.2f}")
        df['EBITDA_Margin'] = df['EBITDA_Margin'].apply(lambda x: f"{x*100:.2f}%")
        
        print(df.to_string(index=False))
        
        print("\n4. TERMINAL VALUE CALCULATION")
        print("-" * 80)
        final_fcf = projections[-1]['FCF']
        print(f"Final Year FCF (FY30):       ${final_fcf:>20,.2f}")
        print(f"Terminal Growth Rate:        {self.terminal_growth*100:>19.2f}%")
        print(f"Terminal Value:              ${ev_calc['terminal_value']:>20,.2f}")
        print(f"PV of Terminal Value:        ${ev_calc['pv_terminal_value']:>20,.2f}")
        
        print("\n5. VALUATION SUMMARY")
        print("-" * 80)
        print(f"PV of Projected FCFs:        ${ev_calc['pv_projected_fcfs']:>20,.2f}")
        print(f"PV of Terminal Value:         ${ev_calc['pv_terminal_value']:>20,.2f}")
        print(f"Enterprise Value:             ${ev_calc['enterprise_value']:>20,.2f}")
        
        equity_value = self.calculate_equity_value(ev_calc['enterprise_value'])
        print(f"Equity Value:                ${equity_value:>20,.2f}")
        
        print(f"\nValuation Multiples:")
        print(f"EV/Revenue:                   {ev_calc['enterprise_value']/self.base_revenue:>19.2f}x")
        print(f"EV/EBITDA:                    {ev_calc['enterprise_value']/self.base_ebitda:>19.2f}x")
        
        print("\n6. SENSITIVITY ANALYSIS")
        print("-" * 80)
        print("\nImpact of WACC (Terminal Growth = 2.5%):")
        print("-" * 80)
        for wacc in [0.08, 0.09, 0.10, 0.11, 0.12]:
            original_wacc = self.wacc
            self.wacc = wacc
            ev_calc = self.calculate_enterprise_value()
            equity = self.calculate_equity_value(ev_calc['enterprise_value'])
            marker = " <-- Base Case" if wacc == 0.10 else ""
            print(f"WACC {wacc*100:.0f}%:  EV = ${ev_calc['enterprise_value']:>12,.0f}  Equity = ${equity:>12,.0f}{marker}")
            self.wacc = original_wacc
        
        print("\nImpact of Terminal Growth (WACC = 10%):")
        print("-" * 80)
        for growth in [0.015, 0.020, 0.025, 0.030, 0.035]:
            original_growth = self.terminal_growth
            self.terminal_growth = growth
            ev_calc = self.calculate_enterprise_value()
            equity = self.calculate_equity_value(ev_calc['enterprise_value'])
            marker = " <-- Base Case" if growth == 0.025 else ""
            print(f"Growth {growth*100:.2f}%:  EV = ${ev_calc['enterprise_value']:>12,.0f}  Equity = ${equity:>12,.0f}{marker}")
            self.terminal_growth = original_growth
        
        print("\n" + "=" * 80)
        print("END OF REPORT")
        print("=" * 80)
        
        return ev_calc, equity_value

if __name__ == "__main__":
    # Create DCF valuation instance
    dcf = DCFValuationFY25()
    
    # Generate comprehensive report
    ev_calc, equity_value = dcf.generate_report()
    
    # Export projections to CSV
    projections_df = pd.DataFrame(ev_calc['projections'])
    projections_df.to_csv('dcf_projections_fy25.csv', index=False)
    print("\nProjections exported to: dcf_projections_fy25.csv")
    
    # Export sensitivity analysis
    sensitivity_df = dcf.sensitivity_analysis()
    sensitivity_df.to_csv('dcf_sensitivity_analysis_fy25.csv', index=False)
    print("Sensitivity analysis exported to: dcf_sensitivity_analysis_fy25.csv")


