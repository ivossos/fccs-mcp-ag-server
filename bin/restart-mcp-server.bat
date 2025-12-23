@echo off
REM Restart MCP Server Script

echo Restarting FCCS MCP Server...

if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run setup-windows.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking for running processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *mcp*" 2>nul

echo.
echo Starting MCP Server...
echo Note: If using Claude Desktop, restart Claude Desktop instead.
echo.

python -m cli.mcp_server

