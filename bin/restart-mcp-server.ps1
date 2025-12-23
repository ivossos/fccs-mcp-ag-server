# Restart MCP Server Script
Write-Host "Restarting FCCS MCP Server..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup-windows.bat first." -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Check for running Python processes related to MCP
Write-Host "Checking for running MCP server processes..." -ForegroundColor Yellow
$mcpProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*fccs-mcp-ag-server*" -or 
    $_.CommandLine -like "*mcp_server*"
}

if ($mcpProcesses) {
    Write-Host "Found running MCP server processes. Stopping..." -ForegroundColor Yellow
    $mcpProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "Starting MCP Server..." -ForegroundColor Green
Write-Host "Note: If using Claude Desktop, restart Claude Desktop instead." -ForegroundColor Yellow
Write-Host ""

# Start the MCP server
python -m cli.mcp_server

