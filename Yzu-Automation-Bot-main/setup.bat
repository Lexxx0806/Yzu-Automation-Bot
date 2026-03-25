@echo off
title School Downloader - Setup
echo.
echo ============================================
echo   School Portal Downloader - SETUP
echo ============================================
echo.
echo This will install everything you need.
echo Please wait, this may take a few minutes...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed on your computer!
    echo.
    echo Please do this first:
    echo  1. Open your browser and go to: https://www.python.org/downloads/
    echo  2. Click the big yellow "Download Python" button
    echo  3. Run the installer - IMPORTANT: check the box that says
    echo     "Add Python to PATH" before clicking Install
    echo  4. After installing, run this setup.bat again
    echo.
    pause
    exit /b 1
)

echo [OK] Python found!
echo.

REM Install pip packages
echo Installing required packages...
echo.
python -m pip install --upgrade pip
python -m pip install playwright

echo.
echo Installing browser engine (Chromium)...
python -m playwright install chromium

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo NEXT STEPS:
echo  1. Open config.json with Notepad
echo  2. Replace "https://your-school-portal.edu" with your real portal URL
echo  3. Replace "C:/Users/YourName/Downloads/SchoolFiles" with your actual
echo     Windows username (check what it says in C:\Users\)
echo  4. Set your course name and week label
echo  5. Save the file, then double-click run.bat to start!
echo.
pause
