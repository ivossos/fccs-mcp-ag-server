@echo off
REM Quick script to install/update dependencies

echo Installing/Updating dependencies...
echo.

if not exist "venv" (
    echo Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e .

echo.
echo [OK] Dependencies installed/updated
pause












