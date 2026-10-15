@echo off
title AI Resume Analyzer — Backend Server
color 0A

echo.
echo  ============================================================
echo    AI Resume Analyzer — Starting Backend Server
echo  ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Navigate to backend folder
cd /d "%~dp0backend"

:: Install dependencies
echo  [1/3] Installing Python dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    echo  Try running: pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo  [2/3] Dependencies installed successfully.
echo.
echo  [3/3] Starting Flask server...
echo.
echo  ============================================================
echo    Backend running at: http://localhost:5000
echo    Health Check:       http://localhost:5000/health
echo    Sample Analysis:    http://localhost:5000/api/analyze-sample
echo  ============================================================
echo.
echo  Open index.html in your browser to use the app.
echo  Press Ctrl+C to stop the server.
echo.

:: Start Flask server
python app.py

pause
