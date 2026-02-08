@echo off
REM Django Music Backend - Quick Start Script for Windows

echo ==================================
echo Django Music Backend Setup
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3 is not installed. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [OK] Python 3 found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q Django djangorestframework django-cors-headers python-dotenv

echo [OK] Dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env >nul 2>&1
    echo [OK] .env file created (please update with your settings)
)

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

echo [OK] Database migrations complete

REM Ask if user wants to create a superuser
echo.
set /p CREATE_SUPERUSER="Do you want to create a superuser for the admin panel? (y/n): "
if /i "%CREATE_SUPERUSER%"=="y" (
    python manage.py createsuperuser
)

REM Ask if user wants to seed data
echo.
set /p SEED_DATA="Do you want to seed the database with sample data? (y/n): "
if /i "%SEED_DATA%"=="y" (
    python manage.py seed_data
)

echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo To start the server, run:
echo   venv\Scripts\activate
echo   python manage.py runserver 0.0.0.0:5000
echo.
echo API will be available at: http://localhost:5000/api/
echo Admin panel at: http://localhost:5000/admin/
echo.
pause
