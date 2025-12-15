@echo off
REM Start the MCP server (for Claude Desktop)

if not exist "venv" (
    echo Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Starting FCCS MCP Server...
echo This server communicates via stdio for Claude Desktop
echo.
python -m cli.mcp_server


