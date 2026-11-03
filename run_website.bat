@echo off
title ShopKart India - E-Commerce Web Application
echo ======================================================================
echo   ShopKart India - Local Development Web Server Launcher
echo ======================================================================
echo.

:: 1. Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH.
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: 2. Create .env from .env.example if missing
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing .env configuration from .env.example...
        copy .env.example .env >nul
    )
)

:: 3. Install required dependencies
echo [*] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet

:: 4. Run database migrations
echo [*] Applying database migrations...
python manage.py migrate --noinput

:: 5. Populate initial database seed if empty
if not exist "db.sqlite3" (
    echo [*] Seeding Indian product catalog and demo accounts...
    python seed.py
)

:: 6. Launch default browser
echo [*] Launching ShopKart India in your default browser...
start "" "http://127.0.0.1:8000/"

:: 7. Start Django development server
echo.
echo ======================================================================
echo   Website running at: http://127.0.0.1:8000/
echo   Admin Dashboard:    http://127.0.0.1:8000/admin-dashboard/
echo   Django Admin:       http://127.0.0.1:8000/admin/
echo.
echo   Demo Credentials:
echo     - Admin:    admin / Admin@123
echo     - Customer: rahul / Password@123
echo.
echo   Press [Ctrl + C] in this window to stop the server.
echo ======================================================================
echo.
python manage.py runserver 127.0.0.1:8000
pause
