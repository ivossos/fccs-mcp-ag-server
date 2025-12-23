@echo off
REM Batch script to run Python scripts easily
REM Usage: run_python_script.bat script_name.py [arguments]

if "%~1"=="" (
    echo [ERROR] Please provide a script name
    echo Usage: run_python_script.bat script_name.py [arguments]
    exit /b 1
)

set SCRIPT_NAME=%~1
shift

REM Check if script exists
if not exist "%SCRIPT_NAME%" (
    echo [ERROR] Script not found: %SCRIPT_NAME%
    echo Current directory: %CD%
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the script
echo [INFO] Running: python %SCRIPT_NAME% %*
echo.

python %SCRIPT_NAME% %*

if errorlevel 1 (
    echo.
    echo [ERROR] Script exited with error code: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
) else (
    echo.
    echo [OK] Script completed successfully
)



