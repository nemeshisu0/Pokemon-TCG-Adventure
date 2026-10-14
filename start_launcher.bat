@echo off
REM ==============================================================================
REM Pokémon TCG Adventure — Windows Launcher Script
REM Compatible with: Windows 10 & Windows 11 (64-bit)
REM ==============================================================================

echo ==================================================
echo  Starting Pokemon TCG Adventure - Windows Launcher
echo ==================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

set VENV_DIR=%SCRIPT_DIR%venv_win
if not exist "%VENV_DIR%" (
    echo [INFO] Creating Python virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    "%VENV_DIR%\Scripts\pip.exe" install --upgrade pip
    echo [INFO] Installing dependencies from requirements.txt...
    "%VENV_DIR%\Scripts\pip.exe" install -r "%SCRIPT_DIR%requirements.txt"
)

set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%
"%VENV_DIR%\Scripts\python.exe" "%SCRIPT_DIR%launcher\launcher_window.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Launcher closed with code %ERRORLEVEL%.
    pause
)
