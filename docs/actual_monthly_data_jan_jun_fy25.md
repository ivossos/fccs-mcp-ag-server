# Actual Monthly Data for Jan-Jun FY25
## Calculated from YTD Values in FCCS

**Date:** Generated from FCCS system query  
**Scenario:** Actual  
**Year:** FY25  
**Entity:** FCCS_Entity Total (Consolidated)

---

## Summary

**The statement "Actual monthly data for EBITDA, Operating Income, Net Income, and CapEx was not available for Jan-Jun" is PARTIALLY TRUE:**

- ✅ **YTD (Year-to-Date) data IS available** for all four metrics for Jan-Jun
- ❌ **Monthly incremental values are NOT directly stored** - they must be calculated from YTD differences
- ✅ **Monthly values CAN be calculated** by subtracting previous month's YTD from current month's YTD

---

## YTD Data Retrieved from FCCS

### EBITDA (Year-to-Date)
| Month | YTD Value |
|-------|-----------|
| Jan   | $951,091.53 |
| Feb   | $2,281,456.07 |
| Mar   | $6,643,665.68 |
| Apr   | $11,162,422.05 |
| May   | $15,590,780.65 |
| Jun   | $19,954,853.75 |

### Operating Income (Year-to-Date)
| Month | YTD Value |
|-------|-----------|
| Jan   | $759,224.32 |
| Feb   | $2,337,115.01 |
| Mar   | $6,993,966.82 |
| Apr   | $11,552,093.81 |
| May   | $15,969,890.54 |
| Jun   | $20,282,175.39 |

### Net Income (Year-to-Date)
| Month | YTD Value |
|-------|-----------|
| Jan   | -$2,807,253.86 |
| Feb   | -$4,937,767.49 |
| Mar   | -$5,904,644.22 |
| Apr   | -$5,704,859.34 |
| May   | -$5,628,391.31 |
| Jun   | -$5,370,481.95 |

### Capital Expenditure Additions (Year-to-Date)
| Month | YTD Value |
|-------|-----------|
| Jan   | $369,549.75 |
| Feb   | $1,148,845.83 |
| Mar   | $1,213,326.46 |
| Apr   | $1,177,582.43 |
| May   | $1,104,253.16 |
| Jun   | $1,179,592.57 |

---

## Calculated Monthly Incremental Values

### EBITDA (Monthly)
| Month | Monthly Value | Calculation |
|-------|---------------|-------------|
| Jan   | $951,091.53 | YTD Jan |
| Feb   | $1,330,364.54 | YTD Feb - YTD Jan = $2,281,456.07 - $951,091.53 |
| Mar   | $4,362,209.61 | YTD Mar - YTD Feb = $6,643,665.68 - $2,281,456.07 |
| Apr   | $4,518,756.37 | YTD Apr - YTD Mar = $11,162,422.05 - $6,643,665.68 |
| May   | $4,428,358.60 | YTD May - YTD Apr = $15,590,780.65 - $11,162,422.05 |
| Jun   | $4,364,073.10 | YTD Jun - YTD May = $19,954,853.75 - $15,590,780.65 |

**Total Jan-Jun:** $19,954,853.75 (matches Jun YTD)

### Operating Income (Monthly)
| Month | Monthly Value | Calculation |
|-------|---------------|-------------|
| Jan   | $759,224.32 | YTD Jan |
| Feb   | $1,577,890.69 | YTD Feb - YTD Jan = $2,337,115.01 - $759,224.32 |
| Mar   | $4,656,851.81 | YTD Mar - YTD Feb = $6,993,966.82 - $2,337,115.01 |
| Apr   | $4,558,126.99 | YTD Apr - YTD Mar = $11,552,093.81 - $6,993,966.82 |
| May   | $4,417,796.73 | YTD May - YTD Apr = $15,969,890.54 - $11,552,093.81 |
| Jun   | $4,312,284.85 | YTD Jun - YTD May = $20,282,175.39 - $15,969,890.54 |

**Total Jan-Jun:** $20,282,175.39 (matches Jun YTD)

### Net Income (Monthly)
| Month | Monthly Value | Calculation |
|-------|---------------|-------------|
| Jan   | -$2,807,253.86 | YTD Jan |
| Feb   | -$2,130,513.63 | YTD Feb - YTD Jan = -$4,937,767.49 - (-$2,807,253.86) |
| Mar   | -$966,876.73 | YTD Mar - YTD Feb = -$5,904,644.22 - (-$4,937,767.49) |
| Apr   | $199,784.88 | YTD Apr - YTD Mar = -$5,704,859.34 - (-$5,904,644.22) |
| May   | $76,468.03 | YTD May - YTD Apr = -$5,628,391.31 - (-$5,704,859.34) |
| Jun   | $257,909.36 | YTD Jun - YTD May = -$5,370,481.95 - (-$5,628,391.31) |

**Total Jan-Jun:** -$5,370,481.95 (matches Jun YTD)

**Note:** Net Income shows improvement trend - negative in Q1, turning positive in Q2.

### Capital Expenditure Additions (Monthly)
| Month | Monthly Value | Calculation |
|-------|---------------|-------------|
| Jan   | $369,549.75 | YTD Jan |
| Feb   | $779,296.08 | YTD Feb - YTD Jan = $1,148,845.83 - $369,549.75 |
| Mar   | $64,480.63 | YTD Mar - YTD Feb = $1,213,326.46 - $1,148,845.83 |
| Apr   | -$35,744.03 | YTD Apr - YTD Mar = $1,177,582.43 - $1,213,326.46 |
| May   | -$73,329.27 | YTD May - YTD Apr = $1,104,253.16 - $1,177,582.43 |
| Jun   | $75,339.41 | YTD Jun - YTD May = $1,179,592.57 - $1,104,253.16 |

**Total Jan-Jun:** $1,179,592.57 (matches Jun YTD)

**Note:** Negative values in Apr and May suggest disposals/adjustments exceeding additions in those months.

---

## Key Findings

1. **Data Availability:** YTD data exists for all four metrics (EBITDA, Operating Income, Net Income, CapEx) for Jan-Jun FY25
2. **Data Format:** Data is stored as cumulative YTD values, not as monthly increments
3. **Monthly Calculation:** Monthly values can be accurately calculated by taking the difference between consecutive YTD values
4. **Data Quality:** All calculated totals match the June YTD values, confirming calculation accuracy

---

## Comparison with Previous Assumption

The file `generate_synthetic_fy25_data.py` assumed these values were `None` for Jan-Jun:
- EBITDA: None
- Operating Income: None  
- Net Income: None
- CapEx: None

**However, actual YTD data IS available in FCCS** and monthly values can be calculated as shown above.

---

## Recommendations

1. **Update Data Scripts:** The `generate_synthetic_fy25_data.py` script should be updated to use actual YTD data from FCCS instead of assuming `None`
2. **Data Storage:** Consider whether monthly incremental values should be stored separately, or if calculating from YTD is sufficient
3. **Documentation:** Update documentation to clarify that monthly values are derived from YTD differences

---

*Generated from FCCS system queries via MCP FCCS Agent*


