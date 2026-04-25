@echo off
setlocal enabledelayedexpansion

REM ====================================
REM   POKER BOT LAUNCHER - HACKER MODE
REM ====================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║  ⚡ POKER BOT NEURAL INTERFACE - INITIALIZING ⚡          ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if we're in the right directory
if not exist "hacker_gui.py" (
    echo [ERROR] hacker_gui.py not found!
    echo [INFO] Please run this from the Back_end directory
    echo.
    pause
    exit /b 1
)

REM Check Python installation
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH!
    echo [INFO] Please install Python 3.8+ from https://www.python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check required packages
echo [*] Verifying dependencies...
python -c "import anthropic" >nul 2>&1
if errorlevel 1 (
    echo [!] Missing anthropic package, installing...
    pip install anthropic -q
)

python -c "import easyocr" >nul 2>&1
if errorlevel 1 (
    echo [!] Missing easyocr package, installing...
    pip install easyocr -q
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo [!] Missing Pillow package, installing...
    pip install Pillow -q
)

python -c "import mss" >nul 2>&1
if errorlevel 1 (
    echo [!] Missing mss package, installing...
    pip install mss -q
)

REM Check .env file
echo [*] Checking configuration...
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo [INFO] Creating .env template...
    (
        echo CLAUDE_API_KEY=your-api-key-here
        echo ANALYSIS_INTERVAL=3
        echo GOOGLE_APPLICATION_CREDENTIALS=C:\Users\ivane\Documents\GitHub\Poker-Bot\Back_end\credentials\pokerbot-493518-65f60dcebe77.json
    ) > .env
    echo [!] Please add your CLAUDE_API_KEY to .env file!
    echo [!] Get one at https://console.anthropic.com
    echo.
    pause
)

REM Check for Claude API key
for /f "tokens=2 delims==" %%a in ('findstr /I "CLAUDE_API_KEY=" .env') do set API_KEY=%%a
if "!API_KEY!"=="your-api-key-here" (
    echo [ERROR] CLAUDE_API_KEY not configured!
    echo [INFO] Please edit .env and add your API key
    echo [INFO] Get one at https://console.anthropic.com
    echo.
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    SYSTEM READY                            ║
echo ║              Launching Neural Interface...                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Launch the GUI
python hacker_gui.py

REM If we get here, the program closed
echo.
echo [*] Neural interface terminated.
echo.
pause
