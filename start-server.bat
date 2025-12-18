@echo off
REM Start the web server

if not exist "venv" (
    echo Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Starting FCCS MCP Web Server...
echo Server will be available at http://localhost:8080
echo Press Ctrl+C to stop
echo.
python -m web.server










