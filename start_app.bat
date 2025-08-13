@echo off
setlocal enabledelayedexpansion

echo === Product Search Tool ===
echo Starting the application...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Kill any existing processes
echo Stopping existing processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start backend
echo Starting backend...
cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Warning: Some dependencies may not have installed correctly
)

REM Start backend
echo Starting backend server...
start "Backend" cmd /k "venv\Scripts\activate.bat && python app.py"
cd ..

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

REM Check if backend is running
echo Checking if backend is running...
curl -f http://localhost:5003/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Backend may not be running properly
    echo Please check the backend window for errors
)

REM Start frontend
echo Starting frontend...
cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo Error: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

REM Start frontend
echo Starting frontend server...
start "Frontend" cmd /k "npm start"
cd ..

REM Wait for frontend to start
echo Waiting for frontend to start...
timeout /t 10 /nobreak >nul

echo.
echo === Application is running! ===
echo Backend: http://localhost:5003
echo Frontend: http://localhost:3000
echo.
echo Open http://localhost:3000 in your browser
echo.
echo Press any key to stop the application...

pause >nul

REM Stop processes
echo Stopping application...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul
echo Application stopped. 