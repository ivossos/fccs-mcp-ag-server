# PowerShell script to run Python scripts easily
# Usage: .\run_python_script.ps1 script_name.py [arguments]

param(
    [Parameter(Mandatory=$true)]
    [string]$ScriptName,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Check if script exists
if (-not (Test-Path $ScriptName)) {
    Write-Host "[ERROR] Script not found: $ScriptName" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
    & "venv\Scripts\activate.bat"
}

# Run the script
Write-Host "[INFO] Running: python $ScriptName $($Arguments -join ' ')" -ForegroundColor Cyan
Write-Host ""

python $ScriptName $Arguments

$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "[OK] Script completed successfully" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Script exited with code: $exitCode" -ForegroundColor Red
}

exit $exitCode



