@echo off
chcp 65001 >nul
title Knesset Project Launcher

echo ══════════════════════════════════════════════════════════
echo   Knesset Project - Starting All Services
echo ══════════════════════════════════════════════════════════
echo.

:: Check for virtual environment
if exist "%~dp0Keneset new\venv\Scripts\activate.bat" (
    call "%~dp0Keneset new\venv\Scripts\activate.bat"
    echo [OK] Virtual environment activated
) else (
    echo [!] No venv found, using system Python
)

:: Install requests if needed
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [*] Installing 'requests' library...
    pip install requests >nul 2>&1
    echo [OK] requests installed
)

echo.
echo ── Starting Deot Web Service (port 5000) ──
start "Deot Web Service" cmd /c "cd /d "%~dp0web services" && python app.py"
echo [OK] Web Service starting on http://localhost:5000

:: Wait a moment for the Web Service to start
timeout /t 2 /nobreak >nul

echo.
echo ── Starting Main Website (port 3000) ──
start "Knesset Website" cmd /c "cd /d "%~dp0Keneset new" && python app.py"
echo [OK] Website starting on http://localhost:3000

echo.
echo ══════════════════════════════════════════════════════════
echo   Both services are running!
echo   Website:     http://localhost:3000
echo   Web Service: http://localhost:5000/api/deot
echo ══════════════════════════════════════════════════════════
echo.
echo Press any key to open the website in browser...
pause >nul

start http://localhost:3000
