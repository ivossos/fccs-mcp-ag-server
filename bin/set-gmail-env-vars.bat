@echo off
REM Gmail MCP Server Environment Variables Setup Script (Batch)
REM This script sets up Gmail environment variables for the current user

echo Gmail MCP Server Environment Variables Setup
echo =============================================
echo.

REM Prompt for credentials file path
set /p CREDENTIALS_PATH="Enter the full path to your Gmail credentials JSON file (e.g., C:\Users\YourName\credentials.json): "

REM Check if file exists
if not exist "%CREDENTIALS_PATH%" (
    echo Error: File not found at: %CREDENTIALS_PATH%
    echo Please check the path and try again.
    pause
    exit /b 1
)

REM Prompt for token file path
set /p TOKEN_PATH="Enter the full path where the Gmail token should be stored (e.g., C:\Users\YourName\token.json): "

REM Create directory if it doesn't exist
for %%F in ("%TOKEN_PATH%") do set TOKEN_DIR=%%~dpF
if not exist "%TOKEN_DIR%" (
    echo Creating directory: %TOKEN_DIR%
    mkdir "%TOKEN_DIR%"
)

REM Set environment variables permanently for current user
echo.
echo Setting environment variables...
setx GMAIL_CREDENTIALS_PATH "%CREDENTIALS_PATH%"
setx GMAIL_TOKEN_PATH "%TOKEN_PATH%"

echo.
echo Environment variables set successfully!
echo.
echo Current values:
echo   GMAIL_CREDENTIALS_PATH = %CREDENTIALS_PATH%
echo   GMAIL_TOKEN_PATH = %TOKEN_PATH%
echo.
echo Note: Please restart Cursor for the changes to take effect.
echo.

pause













