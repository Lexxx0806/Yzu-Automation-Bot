#!/bin/bash
echo ""
echo "============================================"
echo "  School Portal Downloader - SETUP"
echo "============================================"
echo ""
echo "This will install everything you need."
echo "Please wait, this may take a few minutes..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python is not installed!"
    echo ""
    echo "Please do this first:"
    echo "  1. Go to: https://www.python.org/downloads/"
    echo "  2. Download and install Python 3"
    echo "  3. After installing, run this script again:"
    echo "       bash setup.sh"
    echo ""
    exit 1
fi

echo "[OK] Python found!"
echo ""

echo "Installing required packages..."
echo ""
python3 -m pip install --upgrade pip
python3 -m pip install playwright python-dotenv

echo ""
echo "Installing browser engine (Chromium)..."
python3 -m playwright install chromium

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "NEXT STEPS:"
echo "  1. Create a .env file with your YZU credentials:"
echo "       YZU_USERNAME=your_student_id"
echo "       YZU_PASSWORD=your_password"
echo "  2. (Optional) Edit download_folder in config.json"
echo "       Default save location: ~/Downloads/School Files"
echo "  3. Start the bot: bash run.sh"
echo ""
