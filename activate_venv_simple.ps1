# Simple activation script - Run with: powershell -ExecutionPolicy Bypass -File .\activate_venv_simple.ps1
# Or copy-paste the commands below into your PowerShell session

$projectPath = "E:\MCPServer\fccs-mcp-ag-server-main"
$venvPath = Join-Path $projectPath "venv"

if (Test-Path $venvPath) {
    $env:VIRTUAL_ENV = $venvPath
    $env:PATH = "$($venvPath)\Scripts;$env:PATH"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host "VIRTUAL_ENV: $env:VIRTUAL_ENV" -ForegroundColor Cyan
} else {
    Write-Host "Error: Virtual environment not found at $venvPath" -ForegroundColor Red
}







