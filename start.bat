@echo off
echo ================================
echo   Decision Anchor - 決策錨點
echo ================================
echo.

:: Start Python backend
start "DA-Backend" cmd /k "cd /d %~dp0backend && python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start Vite frontend
start "DA-Frontend" cmd /k "set PATH=%PATH%;C:\Program Files\nodejs && cd /d %~dp0frontend2 && npm run dev"

echo.
echo  Backend API:  http://localhost:8000
echo  Frontend:     http://localhost:3000
echo.
echo  *** iPhone 手機輸入以下網址 ***
echo  先查詢IP: ipconfig ^| findstr IPv4
echo  然後用: http://[你的IP]:3000
echo  目前網路IP: 192.168.0.136
echo.
pause >nul
