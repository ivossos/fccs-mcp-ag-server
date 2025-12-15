@echo off
REM Initialize the database

if not exist "venv" (
    echo Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Initializing database...
echo.
python scripts\init_db.py
echo.
pause


