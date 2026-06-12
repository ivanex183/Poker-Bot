@echo off
setlocal enabledelayedexpansion

REM ====================================
REM   POKER BOT LAUNCHER
REM ====================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║  🎰 POKER BOT - REAL-TIME ANALYZER 🎰                     ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check Python installation
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH!
    echo [INFO] Please install Python 3.14+ from https://www.python.org
    echo.
    pause
    exit /b 1
)

REM Check required packages
echo [*] Verifying dependencies...

for %%P in (easyocr mss Pillow python-dotenv cv2 ultralytics) do (
    python -c "import %%P" >nul 2>&1
    if errorlevel 1 (
        echo [!] Installing %%P...
        pip install %%P -q
    )
)

echo [✓] All dependencies ready!
echo.

REM Navigate to Front_end
cd ..\Front_end

echo ╔════════════════════════════════════════════════════════════╗
echo ║              LAUNCHING GUI APPLICATION                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Launch the GUI
python gui.py

REM If we get here, the program closed
echo.
echo [*] Application terminated.
echo.
pause
