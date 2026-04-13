@echo off
cd /d "%~dp0"
echo Starting Knesset Database Website...

:: Check if the virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo Virtual environment not found. Setting up for the first time...
    echo This may take a few minutes...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python is installed.
        pause
        exit /b 1
    )
    echo Installing required libraries...
    "venv\Scripts\python.exe" -m pip install --upgrade pip
    "venv\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
    echo Setup complete!
)

echo This window will run the server. Close it to stop the website.
echo.

:: Open the browser after a short delay (spawned in background)
start "" cmd /c "timeout /t 3 /nobreak > NUL && start http://localhost:3000"

:: Start the Python Flask app using the virtual environment (runs in foreground)
"venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo.
    echo An error occurred while running the website.
    pause
)

echo.
pause
