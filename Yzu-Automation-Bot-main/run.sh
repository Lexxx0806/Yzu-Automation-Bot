#!/bin/bash
echo ""
echo "============================================"
echo "  School Portal File Downloader"
echo "============================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found. Please run setup.sh first!"
    echo "        Run with: bash setup.sh"
    exit 1
fi

python3 "$(dirname "$0")/downloader.py"
