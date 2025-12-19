# Gmail MCP Server Environment Variables Setup Script
# Run this script in PowerShell to set up Gmail environment variables

Write-Host "Gmail MCP Server Environment Variables Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Note: Running without administrator privileges. Variables will be set for current user only." -ForegroundColor Yellow
    Write-Host ""
}

# Prompt for credentials file path
$credentialsPath = Read-Host "Enter the full path to your Gmail credentials JSON file (e.g., C:\Users\YourName\credentials.json)"
if (-not (Test-Path $credentialsPath)) {
    Write-Host "Error: File not found at: $credentialsPath" -ForegroundColor Red
    Write-Host "Please check the path and try again." -ForegroundColor Red
    exit 1
}

# Prompt for token file path (can be created if doesn't exist)
$tokenPath = Read-Host "Enter the full path where the Gmail token should be stored (e.g., C:\Users\YourName\token.json)"
$tokenDir = Split-Path $tokenPath -Parent
if (-not (Test-Path $tokenDir)) {
    Write-Host "Creating directory: $tokenDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $tokenDir -Force | Out-Null
}

# Set environment variables
Write-Host ""
Write-Host "Setting environment variables..." -ForegroundColor Green

# Set for current session
$env:GMAIL_CREDENTIALS_PATH = $credentialsPath
$env:GMAIL_TOKEN_PATH = $tokenPath

# Set permanently for user
[System.Environment]::SetEnvironmentVariable("GMAIL_CREDENTIALS_PATH", $credentialsPath, "User")
[System.Environment]::SetEnvironmentVariable("GMAIL_TOKEN_PATH", $tokenPath, "User")

Write-Host "✓ Environment variables set successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Current values:" -ForegroundColor Cyan
Write-Host "  GMAIL_CREDENTIALS_PATH = $credentialsPath"
Write-Host "  GMAIL_TOKEN_PATH = $tokenPath"
Write-Host ""
Write-Host "Note: Please restart Cursor for the changes to take effect." -ForegroundColor Yellow
Write-Host ""

# Verify
Write-Host "Verifying environment variables..." -ForegroundColor Cyan
$credVar = [System.Environment]::GetEnvironmentVariable("GMAIL_CREDENTIALS_PATH", "User")
$tokenVar = [System.Environment]::GetEnvironmentVariable("GMAIL_TOKEN_PATH", "User")

if ($credVar -and $tokenVar) {
    Write-Host "✓ Verification successful!" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: Variables may not be set correctly. Please check manually." -ForegroundColor Yellow
}











