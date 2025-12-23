# FCCS Performance Dashboard

Interactive web dashboard for visualizing FCCS performance data, top performers, underperformers, and entity trends.

## Features

- 📊 **Key Metrics**: Consolidated Net Income, Year, Application status
- 🏆 **Top Performers**: Top N entities by Net Income with interactive charts
- ⚠️ **Underperformers**: Bottom N entities requiring attention
- 📈 **Performance Trends**: Monthly performance analysis for selected entities
- 🔄 **Real-time Data**: Live data from FCCS system

## Installation

Install dashboard dependencies:

```bash
pip install streamlit plotly pandas
```

Or add to `pyproject.toml`:

```toml
[project.optional-dependencies]
dashboard = [
    "streamlit>=1.28.0",
    "plotly>=5.17.0",
    "pandas>=2.0.0",
]
```

## Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Sections

### 1. Key Metrics
- Consolidated Net Income for selected year
- Current year and scenario
- Application status

### 2. Top Performers
- Interactive bar chart showing top N performers
- Sortable table with rankings
- Color-coded by performance

### 3. Underperformers
- Interactive bar chart showing bottom N performers
- Identifies entities requiring attention
- Red color scheme for losses

### 4. Entity Performance Trend
- Select any entity from top/bottom performers
- Monthly performance trend line chart
- Monthly change calculations
- Break-even line indicator

## Configuration

Use the sidebar to:
- Select year (FY24 or FY25)
- Adjust number of top/bottom performers to display
- Refresh data

## Notes

- Dashboard connects to FCCS using your `.env` configuration
- Data is cached for performance
- Click "Refresh Data" to reload from FCCS
- Entity selection limited to top 100 for performance














