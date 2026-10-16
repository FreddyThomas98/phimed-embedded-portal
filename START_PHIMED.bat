@echo off
title Phimed Client Portal

echo ==========================================
echo       PHIMED CLIENT PORTAL
echo ==========================================
echo.

REM Resolve the root directory of this project
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

REM Automatically free ports 8000 and 5500 if previous instances are still running
echo Checking and freeing ports 8000 and 5500...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /f /t /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5500 " ^| findstr "LISTENING"') do taskkill /f /t /pid %%a >nul 2>&1

REM Start FastAPI backend
echo Starting FastAPI backend...
start "PHIMED Backend" /d "%ROOT_DIR%\backend" cmd /k ""%ROOT_DIR%\backend\venv\Scripts\python.exe" -m uvicorn main:app --reload"

REM Give backend a moment to start
ping 127.0.0.1 -n 4 >nul

REM Start frontend web server
echo Starting frontend...
start "PHIMED Frontend" /d "%ROOT_DIR%\frontend" cmd /k ""%ROOT_DIR%\backend\venv\Scripts\python.exe" -m http.server 5500"

REM Give frontend a moment to start
ping 127.0.0.1 -n 3 >nul

REM Open the portal
echo Opening Phimed Client Portal...
start "" "http://127.0.0.1:5500"

echo.
echo PHIMED Client Portal started.
echo.
exit
