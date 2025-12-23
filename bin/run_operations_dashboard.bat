@echo off
echo Starting Operations Dashboard (Tool Statistics)...
echo.

REM Activate virtual environment and run dashboard
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated!
echo Dashboard will open at: http://localhost:8501
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run tool_stats_dashboard.py



