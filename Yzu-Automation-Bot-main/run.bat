@echo off
title School Portal Downloader
echo.
echo ============================================
echo   School Portal File Downloader
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please run setup.bat first!
    pause
    exit /b 1
)

REM Run the downloader
python "%~dp0downloader.py"

echo.
pause
