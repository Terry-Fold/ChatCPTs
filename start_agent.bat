@echo off
setlocal
title AGAI Agent
cd /d "%~dp0"

set "PYTHON=%LocalAppData%\Microsoft\WindowsApps\python.exe"

if not exist "%PYTHON%" (
    echo Python was not found.
    echo Install Python, then run this file again.
    pause
    exit /b 1
)

"%PYTHON%" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Preparing the agent for its first run...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo The required components could not be installed.
        pause
        exit /b 1
    )
)

echo Starting AGAI Agent...
start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
"%PYTHON%" -m uvicorn agent:app --reload

echo.
echo The agent has stopped.
pause
