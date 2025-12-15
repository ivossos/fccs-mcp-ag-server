# FCCS Performance Dashboard - Quick Start

## 🚀 Quick Start

### 1. Install Dependencies (if not already installed)
```bash
pip install streamlit plotly pandas
```

### 2. Run the Dashboard
```bash
streamlit run dashboard.py
```

Or use the helper script:
- Windows: `run_dashboard.bat`
- Linux/Mac: `bash run_dashboard.sh`

### 3. Access the Dashboard
The dashboard will automatically open in your browser at:
**http://localhost:8501**

## 📊 Dashboard Features

### Key Metrics Section
- Consolidated Net Income for selected year
- Current year and scenario
- Application status

### Top Performers
- Interactive bar chart
- Sortable data table
- Top N entities by Net Income

### Underperformers  
- Interactive bar chart (red theme)
- Bottom N entities requiring attention
- Loss identification

### Entity Performance Trends
- Select any entity from top/bottom lists
- Monthly performance line chart
- Monthly change calculations
- Break-even indicator line

## 🎛️ Configuration

Use the sidebar to:
- **Select Year**: FY24 or FY25
- **Top N Performers**: Slider (5-20 entities)
- **Bottom N Underperformers**: Slider (5-20 entities)
- **Refresh Data**: Reload from FCCS

## 📈 What You Can Do

1. **Identify Best Performers**: See which entities are driving profitability
2. **Spot Underperformers**: Find entities that need attention
3. **Analyze Trends**: View monthly performance for any entity
4. **Make Decisions**: Use data for divestiture or investment decisions

## 🔧 Troubleshooting

### Dashboard won't start
- Check that Streamlit is installed: `pip install streamlit`
- Verify Python version: `python --version` (needs 3.10+)

### Can't connect to FCCS
- Check `.env` file has correct credentials
- Verify FCCS URL is accessible
- Test connection: `python scripts/test_connection.py`

### No data showing
- Click "🔄 Refresh Data" button
- Check that entities exist in cache: `python scripts/check_cache.py`
- Verify year has data loaded in FCCS

## 📝 Notes

- Dashboard uses cached entity data from CSV file
- Data is loaded on-demand for performance
- First load may take a few seconds
- Entity selection limited to top 100 for speed


