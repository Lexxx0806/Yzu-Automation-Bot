@echo off
title School Downloader - GitHub Setup
echo.
echo ============================================
echo   GitHub One-Time Setup
echo ============================================
echo.
echo This will connect your downloader to GitHub
echo so files are automatically pushed after download.
echo.
echo BEFORE YOU START - make sure you have:
echo   [1] A GitHub account (free at https://github.com)
echo   [2] Created an empty repo on GitHub for your school files
echo       (Go to GitHub → click "+" → New repository → name it
echo        something like "school-files" → Create repository)
echo.
pause

REM ── Check git ───────────────────────────────────────────
echo.
echo Checking if Git is installed...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] Git is not installed.
    echo.
    echo Please install it:
    echo   1. Go to: https://git-scm.com/download/win
    echo   2. Download and run the installer
    echo   3. Click Next through all steps (defaults are fine)
    echo   4. After installing, run this setup_github.bat again
    echo.
    pause
    exit /b 1
)
echo [OK] Git is installed!

REM ── Set git identity ────────────────────────────────────
echo.
echo ============================================
echo   Step 1 of 3 — Your Git Identity
echo ============================================
echo.
echo Git needs your name and email to label your commits.
echo Use the same email as your GitHub account.
echo.
set /p GIT_NAME=Enter your name (e.g. John Smith): 
set /p GIT_EMAIL=Enter your GitHub email: 
echo.
git config --global user.name "%GIT_NAME%"
git config --global user.email "%GIT_EMAIL%"
echo [OK] Identity saved!

REM ── GitHub authentication ────────────────────────────────
echo.
echo ============================================
echo   Step 2 of 3 — GitHub Authentication
echo ============================================
echo.
echo The easiest way to authenticate is with GitHub CLI.
echo Let's check if it's installed...
echo.
gh --version >nul 2>&1
if %errorlevel% neq 0 (
    echo GitHub CLI is not installed. Installing now...
    echo.
    echo Please download and install it:
    echo   1. Go to: https://cli.github.com/
    echo   2. Click "Download for Windows"
    echo   3. Run the installer
    echo   4. Come back and run this setup_github.bat again
    echo.
    echo OR if you prefer, you can use a Personal Access Token instead.
    echo See the README.txt for instructions on the token method.
    echo.
    pause
    exit /b 1
)

echo [OK] GitHub CLI found!
echo.
echo Now log in to GitHub. A browser window will open.
echo Sign in to your GitHub account there.
echo.
pause
gh auth login --web -h github.com

echo.
echo ============================================
echo   Step 3 of 3 — Update config.json
echo ============================================
echo.
echo Almost done! Now update your config.json:
echo.
echo   1. Right-click config.json → Open with → Notepad
echo   2. Set "github_repo_url" to your repo URL, like:
echo      "https://github.com/YourUsername/school-files"
echo      (find this on your GitHub repo page)
echo   3. Make sure "github_enabled" is set to: true
echo   4. Save the file
echo.
echo After that, just run run.bat as normal — files will
echo be downloaded AND pushed to GitHub automatically!
echo.
echo ============================================
echo   GitHub setup complete!
echo ============================================
echo.
pause
