@echo off
echo === Decision Anchor Setup ===
echo.

:: Backend
echo [1/2] Installing Python dependencies...
cd /d %~dp0backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

:: Frontend
echo.
echo [2/2] Installing Node dependencies...
cd /d %~dp0frontend
npm install
if errorlevel 1 (
    echo ERROR: npm install failed. Make sure Node.js is installed.
    pause
    exit /b 1
)

echo.
echo === Setup complete ===
echo Run start.bat to launch the app.
pause
