# Run Operations Dashboard (Tool Statistics Dashboard)
# Usage: .\run_operations_dashboard.ps1

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Activate virtual environment
$venvPath = Join-Path $scriptDir "venv"
if (Test-Path $venvPath) {
    $env:VIRTUAL_ENV = $venvPath
    $env:PATH = "$($venvPath)\Scripts;$env:PATH"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "Error: Virtual environment not found at $venvPath" -ForegroundColor Red
    exit 1
}

# Check if streamlit is available
$streamlitPath = Join-Path $venvPath "Scripts\streamlit.exe"
if (-not (Test-Path $streamlitPath)) {
    Write-Host "Error: Streamlit not found. Installing..." -ForegroundColor Yellow
    & "$($venvPath)\Scripts\python.exe" -m pip install streamlit plotly pandas
}

# Run the dashboard
Write-Host "Starting Operations Dashboard..." -ForegroundColor Cyan
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

& "$($venvPath)\Scripts\streamlit.exe" run tool_stats_dashboard.py



