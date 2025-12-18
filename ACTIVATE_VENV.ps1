# Script to activate virtual environment bypassing execution policy
# Usage: .\ACTIVATE_VENV.ps1

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to the project directory (adjust path as needed)
$projectPath = "E:\MCPServer\fccs-mcp-ag-server-main"
if (-not (Test-Path $projectPath)) {
    Write-Host "Project path not found: $projectPath" -ForegroundColor Red
    Write-Host "Please update the path in this script." -ForegroundColor Yellow
    exit 1
}

Set-Location $projectPath

# Activate using Python directly (bypasses execution policy)
$venvPython = Join-Path $projectPath "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host "You can now run Python commands. The venv is active." -ForegroundColor Green
    Write-Host ""
    Write-Host "To use the venv, run commands like:" -ForegroundColor Cyan
    Write-Host "  $venvPython -m pip install <package>" -ForegroundColor Yellow
    Write-Host "  $venvPython your_script.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or set environment variables manually:" -ForegroundColor Cyan
    $env:VIRTUAL_ENV = Join-Path $projectPath "venv"
    $env:PATH = "$($env:VIRTUAL_ENV)\Scripts;$env:PATH"
    Write-Host "VIRTUAL_ENV and PATH updated." -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found at: $venvPython" -ForegroundColor Red
    exit 1
}







