@echo off
echo.
echo ============================================
echo   School Portal File Downloader
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please run setup.bat first!
    pause
    exit /b 1
)

python "%~dp0downloader.py"
pause
