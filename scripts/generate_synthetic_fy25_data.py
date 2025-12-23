"""
Generate Synthetic Data for Missing Months in FY25
Based on actual data patterns from Jan-Jun
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Actual data from FCCS
actual_data = {
    'Jan': {'Sales': 49550540.26, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
    'Feb': {'Sales': 104266202.76, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
    'Mar': {'Sales': 161954835.45, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
    'Apr': {'Sales': 219688679.30, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
    'May': {'Sales': 277317048.57, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
    'Jun': {'Sales': 338615234.06, 'EBITDA': None, 'Operating_Income': None, 'Net_Income': None, 'Cash': None, 'CapEx': None},
}

# Dec YTD totals (target values)
dec_ytd = {
    'Sales': 403932211.85,
    'EBITDA': 23107298.11,
    'Operating_Income': 23520859.01,
    'Net_Income': -6285631.23,
    'Cash': 767034.25,
    'CapEx': 1179592.57
}

def calculate_monthly_increments(ytd_values):
    """Calculate monthly increments from YTD values"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    increments = {}
    
    prev_value = 0
    for month in months:
        increments[month] = ytd_values[month] - prev_value
        prev_value = ytd_values[month]
    
    return increments

def generate_synthetic_data():
    """Generate synthetic monthly data for Jul-Dec"""
    
    # Calculate monthly increments for Jan-Jun
    sales_increments = calculate_monthly_increments({
        'Jan': actual_data['Jan']['Sales'],
        'Feb': actual_data['Feb']['Sales'],
        'Mar': actual_data['Mar']['Sales'],
        'Apr': actual_data['Apr']['Sales'],
        'May': actual_data['May']['Sales'],
        'Jun': actual_data['Jun']['Sales']
    })
    
    # Calculate average monthly increment (excluding Jan which might be partial)
    avg_monthly_sales = np.mean([sales_increments[m] for m in ['Feb', 'Mar', 'Apr', 'May', 'Jun']])
    
    # Calculate remaining sales needed for Jul-Dec
    sales_through_jun = actual_data['Jun']['Sales']
    total_sales_needed = dec_ytd['Sales'] - sales_through_jun
    remaining_months = 6  # Jul-Dec
    
    # Distribute remaining sales across Jul-Dec
    # Use a slight seasonal variation (Q3 typically stronger, Q4 varies)
    monthly_distribution = {
        'Jul': 0.18,  # Slightly above average
        'Aug': 0.17,
        'Sep': 0.16,
        'Oct': 0.17,
        'Nov': 0.16,
        'Dec': 0.16  # Slightly lower due to holidays
    }
    
    # Calculate ratios for other metrics based on Sales
    # EBITDA margin: 5.72% (from Dec YTD)
    # Operating Income margin: ~5.82% (from Dec YTD)
    # Net Income: negative, but improving trend
    # CapEx: ~0.29% of sales (from Dec YTD)
    
    ebitda_margin = dec_ytd['EBITDA'] / dec_ytd['Sales']
    operating_margin = dec_ytd['Operating_Income'] / dec_ytd['Sales']
    net_income_margin = dec_ytd['Net_Income'] / dec_ytd['Sales']
    capex_ratio = dec_ytd['CapEx'] / dec_ytd['Sales']
    
    synthetic_data = {}
    cumulative_sales = sales_through_jun
    cumulative_ebitda = 0  # Will calculate from monthly
    cumulative_operating = 0
    cumulative_net_income = 0
    cumulative_capex = 0
    
    for month in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
        # Calculate monthly sales
        monthly_sales = total_sales_needed * monthly_distribution[month]
        cumulative_sales += monthly_sales
        
        # Calculate other metrics proportionally
        monthly_ebitda = monthly_sales * ebitda_margin
        monthly_operating = monthly_sales * operating_margin
        monthly_net_income = monthly_sales * net_income_margin
        monthly_capex = monthly_sales * capex_ratio
        
        cumulative_ebitda += monthly_ebitda
        cumulative_operating += monthly_operating
        cumulative_net_income += monthly_net_income
        cumulative_capex += monthly_capex
        
        synthetic_data[month] = {
            'Sales': cumulative_sales,
            'EBITDA': cumulative_ebitda,
            'Operating_Income': cumulative_operating,
            'Net_Income': cumulative_net_income,
            'Cash': dec_ytd['Cash'],  # Cash is a balance sheet item, not cumulative
            'CapEx': cumulative_capex
        }
    
    # Adjust to match exact Dec YTD values
    adjustment_factor_sales = dec_ytd['Sales'] / synthetic_data['Dec']['Sales']
    adjustment_factor_ebitda = dec_ytd['EBITDA'] / synthetic_data['Dec']['EBITDA']
    adjustment_factor_operating = dec_ytd['Operating_Income'] / synthetic_data['Dec']['Operating_Income']
    adjustment_factor_net = dec_ytd['Net_Income'] / synthetic_data['Dec']['Net_Income']
    adjustment_factor_capex = dec_ytd['CapEx'] / synthetic_data['Dec']['CapEx']
    
    # Recalculate with adjustments
    cumulative_sales = sales_through_jun
    cumulative_ebitda = 0
    cumulative_operating = 0
    cumulative_net_income = 0
    cumulative_capex = 0
    
    for month in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
        monthly_sales = (total_sales_needed * monthly_distribution[month]) * adjustment_factor_sales
        cumulative_sales += monthly_sales
        
        monthly_ebitda = monthly_sales * ebitda_margin * adjustment_factor_ebitda
        monthly_operating = monthly_sales * operating_margin * adjustment_factor_operating
        monthly_net_income = monthly_sales * net_income_margin * adjustment_factor_net
        monthly_capex = monthly_sales * capex_ratio * adjustment_factor_capex
        
        cumulative_ebitda += monthly_ebitda
        cumulative_operating += monthly_operating
        cumulative_net_income += monthly_net_income
        cumulative_capex += monthly_capex
        
        synthetic_data[month] = {
            'Sales': cumulative_sales,
            'EBITDA': cumulative_ebitda,
            'Operating_Income': cumulative_operating,
            'Net_Income': cumulative_net_income,
            'Cash': dec_ytd['Cash'],
            'CapEx': cumulative_capex
        }
    
    return synthetic_data

def create_complete_dataset():
    """Create complete monthly dataset with actual and synthetic data"""
    
    synthetic = generate_synthetic_data()
    
    # Combine actual and synthetic data
    complete_data = {}
    
    # Add actual data
    for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']:
        complete_data[month] = {
            'Period': month,
            'Sales': actual_data[month]['Sales'],
            'EBITDA': None,  # Not available monthly
            'Operating_Income': None,
            'Net_Income': None,
            'Cash': None,
            'CapEx': None,
            'Data_Type': 'Actual'
        }
    
    # Add synthetic data
    for month in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
        complete_data[month] = {
            'Period': month,
            'Sales': synthetic[month]['Sales'],
            'EBITDA': synthetic[month]['EBITDA'],
            'Operating_Income': synthetic[month]['Operating_Income'],
            'Net_Income': synthetic[month]['Net_Income'],
            'Cash': synthetic[month]['Cash'],
            'CapEx': synthetic[month]['CapEx'],
            'Data_Type': 'Synthetic'
        }
    
    # Create DataFrame
    df = pd.DataFrame.from_dict(complete_data, orient='index')
    
    # Calculate monthly increments
    df['Sales_Increment'] = df['Sales'].diff().fillna(df['Sales'].iloc[0])
    df['EBITDA_Increment'] = df['EBITDA'].diff().fillna(df['EBITDA'].iloc[0] if df['EBITDA'].iloc[0] else 0)
    df['Operating_Increment'] = df['Operating_Income'].diff().fillna(df['Operating_Income'].iloc[0] if df['Operating_Income'].iloc[0] else 0)
    df['Net_Income_Increment'] = df['Net_Income'].diff().fillna(df['Net_Income'].iloc[0] if df['Net_Income'].iloc[0] else 0)
    df['CapEx_Increment'] = df['CapEx'].diff().fillna(df['CapEx'].iloc[0] if df['CapEx'].iloc[0] else 0)
    
    return df

def main():
    print("=" * 80)
    print("SYNTHETIC DATA GENERATION FOR FY25 MISSING MONTHS")
    print("=" * 80)
    
    df = create_complete_dataset()
    
    print("\nComplete Monthly Dataset (YTD Values):")
    print("-" * 80)
    print(df.to_string())
    
    print("\n\nMonthly Increments:")
    print("-" * 80)
    increment_cols = ['Period', 'Sales_Increment', 'EBITDA_Increment', 'Operating_Increment', 
                     'Net_Income_Increment', 'CapEx_Increment', 'Data_Type']
    print(df[increment_cols].to_string())
    
    # Export to CSV
    df.to_csv('fy25_complete_monthly_data.csv', index=False)
    print("\n\nData exported to: fy25_complete_monthly_data.csv")
    
    # Create summary report
    print("\n\nSummary:")
    print("-" * 80)
    print(f"Total Sales (Dec YTD): ${dec_ytd['Sales']:,.2f}")
    print(f"Sales through Jun: ${actual_data['Jun']['Sales']:,.2f}")
    print(f"Sales Jul-Dec (synthetic): ${dec_ytd['Sales'] - actual_data['Jun']['Sales']:,.2f}")
    print(f"\nEBITDA (Dec YTD): ${dec_ytd['EBITDA']:,.2f}")
    print(f"Operating Income (Dec YTD): ${dec_ytd['Operating_Income']:,.2f}")
    print(f"Net Income (Dec YTD): ${dec_ytd['Net_Income']:,.2f}")
    print(f"CapEx (Dec YTD): ${dec_ytd['CapEx']:,.2f}")
    
    # Verify totals match
    print("\n\nVerification:")
    print("-" * 80)
    print(f"Dec Sales matches target: {abs(df.loc['Dec', 'Sales'] - dec_ytd['Sales']) < 0.01}")
    print(f"Dec EBITDA matches target: {abs(df.loc['Dec', 'EBITDA'] - dec_ytd['EBITDA']) < 0.01}")
    print(f"Dec Operating Income matches target: {abs(df.loc['Dec', 'Operating_Income'] - dec_ytd['Operating_Income']) < 0.01}")
    print(f"Dec Net Income matches target: {abs(df.loc['Dec', 'Net_Income'] - dec_ytd['Net_Income']) < 0.01}")
    print(f"Dec CapEx matches target: {abs(df.loc['Dec', 'CapEx'] - dec_ytd['CapEx']) < 0.01}")

if __name__ == "__main__":
    main()


