# Comprehensive Entity Analysis Script

## Overview

The `scripts/comprehensive_entity_analysis.py` script performs a complete entity performance analysis including:

1. **List all FCCS apps** - Retrieves and displays all available FCCS applications
2. **Connect to Consol App** - Establishes connection to the consolidation application
3. **Show top-10 performing entities for actuals 2024** - Identifies best performers by Net Income
4. **Show top-10 underperforming entities for actuals 2024** - Identifies worst performers by Net Income
5. **Simulate divestment for worst performing entity (mid-year 2025)** - Analyzes divestment scenario
6. **Calculate impact on consolidated group** - Quantifies the financial impact of divestment

## Usage

```bash
python scripts/comprehensive_entity_analysis.py
```

## Prerequisites

1. **Environment Configuration**: Ensure `.env` file is configured with:
   - `FCCS_URL`
   - `FCCS_USERNAME`
   - `FCCS_PASSWORD`
   - `FCCS_API_VERSION` (default: "v3")

2. **Entity Cache**: The script requires cached entity data at:
   - `.cache/members/Consol_Entity.json`
   
   If the cache doesn't exist, you can create it using:
   ```bash
   python scripts/create_entity_cache.py
   ```

3. **Database** (optional): For feedback/RL features, ensure PostgreSQL is configured if enabled.

## What the Script Does

### Step 1: List All FCCS Apps
- Connects to FCCS
- Retrieves all available applications
- Displays application names and types
- Identifies "Consol" app if available

### Step 2: Connect to Consol App
- Confirms connection to the consolidation application
- Sets up the application context for subsequent queries

### Step 3: Top 10 Performing Entities (2024)
- Queries Net Income for all individual entities (FY24, Actual, Dec YTD)
- Excludes total/consolidated entities
- Sorts by Net Income (descending)
- Displays top 10 performers with rankings

### Step 4: Top 10 Underperforming Entities (2024)
- Uses the same data from Step 3
- Sorts by Net Income (ascending - lowest first)
- Displays top 10 underperformers with rankings
- Identifies the worst performer

### Step 5: Simulate Divestment (Mid-Year 2025)
- Identifies worst performing entity for FY25
- Retrieves monthly performance data (Jan-Jun)
- Calculates YTD loss at mid-year (June)
- Estimates sale price (50% of annual loss)
- Provides divestment timing analysis

### Step 6: Calculate Consolidated Impact
- Retrieves current consolidated Net Income (FY25)
- Calculates new consolidated Net Income after divestment:
  - New = Current - Entity Loss (June YTD) + Sale Proceeds
- Calculates improvement amount and percentage
- Provides recommendation based on impact

## Output Format

The script provides detailed console output with:
- Formatted tables for rankings
- Financial figures with proper currency formatting
- Clear section separators
- Recommendations based on analysis

## Example Output Structure

```
================================================================================
COMPREHENSIVE ENTITY ANALYSIS
================================================================================

================================================================================
STEP 1: LISTING ALL FCCS APPS
================================================================================
Found 1 application(s):
  1. Consol (Type: FCCS)

[OK] Found 'Consol' app: Consol

================================================================================
STEP 2: CONNECTED TO CONSOL APP
================================================================================
[OK] Connection established

================================================================================
STEP 3: TOP 10 PERFORMING ENTITIES - ACTUALS 2024
================================================================================
TOP 10 PERFORMING ENTITIES - 2024 (Net Income YTD)
Rank    Entity                                              Net Income
--------------------------------------------------------------------------------
1       Entity Name 1                                      $1,234,567.89
...

================================================================================
STEP 4: TOP 10 UNDERPERFORMING ENTITIES - ACTUALS 2024
================================================================================
TOP 10 UNDERPERFORMING ENTITIES - 2024 (Net Income YTD)
Rank    Entity                                              Net Income
--------------------------------------------------------------------------------
1       Worst Entity                                       $-1,234,567.89
...

================================================================================
STEP 5: SIMULATING DIVESTMENT - WORST PERFORMING ENTITY (MID-YEAR 2025)
================================================================================
Worst Performer: Worst Entity
Net Income (FY25 YTD): $-1,234,567.89

Monthly Performance (YTD values):
Month      YTD Net Income
------------------------------
Jan        $-100,000.00
...
Jun        $-500,000.00

Mid-Year 2025 (June) YTD Loss: $-500,000.00
Estimated Sale Price: $617,283.95

================================================================================
STEP 6: CALCULATING IMPACT ON CONSOLIDATED GROUP
================================================================================
DIVESTITURE IMPACT SIMULATION
Metric                                              Amount
--------------------------------------------------------------------------------
Current Consolidated Net Income (FY25 YTD)        $-9,638,049.91
Entity Loss Removed (June YTD)                     $-500,000.00
Estimated Sale Proceeds                            $617,283.95
--------------------------------------------------------------------------------
New Consolidated Net Income                        $-9,520,765.96
Improvement                                        $117,283.95
================================================================================

Percentage Improvement: 1.2%

================================================================================
SUMMARY & RECOMMENDATION
================================================================================
Entity to Divest: Worst Entity
Divestment Date: Mid-Year 2025 (June)
YTD Loss at Divestment: $-500,000.00
Estimated Sale Price: $617,283.95
Expected Improvement: $117,283.95

✅ RECOMMENDATION: Proceed with divestment
   The divestment would improve consolidated results by $117,283.95
```

## Notes

- The script uses cached entity data for efficiency
- Individual entities are filtered (totals/consolidated entities excluded)
- Divestment simulation assumes mid-year 2025 (June)
- Sale price estimation uses 50% of annual loss as a conservative estimate
- All financial figures are in USD (or base currency of the application)

## Troubleshooting

### No Entity Cache
If you see "No entity list available in cache", run:
```bash
python scripts/create_entity_cache.py
```

### No Performance Data
If no performance data is retrieved:
- Verify FY24/FY25 data exists in FCCS
- Check entity names match exactly
- Ensure API credentials are correct
- Verify network connectivity to FCCS

### Connection Issues
- Check `.env` file configuration
- Verify FCCS URL is accessible
- Confirm username/password are correct
- Check API version compatibility



