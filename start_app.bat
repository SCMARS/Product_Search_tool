@echo off
echo === Product Search Tool ===
echo Starting the application...

REM Kill any existing processes
echo Stopping existing processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start backend
echo Starting backend...
cd backend
call venv\Scripts\activate.bat
start "Backend" python app.py
cd ..

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend
echo Starting frontend...
cd frontend
start "Frontend" npm start
cd ..

REM Wait for frontend to start
echo Waiting for frontend to start...
timeout /t 10 /nobreak >nul

echo.
echo === Application is running! ===
echo Backend: http://localhost:5001
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