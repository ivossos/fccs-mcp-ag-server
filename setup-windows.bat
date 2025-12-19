@echo off
REM FCCS MCP Agentic Server - Windows Setup Script
REM This script automates the setup process for Windows deployment

echo ========================================
echo FCCS MCP Agentic Server - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check Python version (3.10+)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
)

REM Install dependencies
echo.
echo Installing dependencies...
echo This may take a few minutes...
pip install -e .
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file from template...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] .env file created
        echo.
        echo [IMPORTANT] Please edit .env file with your configuration:
        echo   - Set FCCS_MOCK_MODE=true for development
        echo   - Configure DATABASE_URL (SQLite or PostgreSQL)
        echo.
        echo Opening .env file in Notepad...
        timeout /t 2 >nul
        notepad .env
    ) else (
        echo [WARNING] .env.example not found, skipping .env creation
    )
) else (
    echo [OK] .env file already exists
)

REM Check if database initialization is needed
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. If using PostgreSQL, initialize the database:
echo    python scripts\init_db.py
echo.
echo 2. Test the connection:
echo    python scripts\test_connection.py
echo.
echo 3. Start the server:
echo    python -m web.server
echo.
echo 4. Or run MCP server:
echo    python -m cli.mcp_server
echo.
echo For more information, see WINDOWS_DEPLOYMENT.md
echo.
pause












