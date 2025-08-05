@echo off
REM Product Search Tool - Windows Batch Startup Script
REM This is a simple alternative to the PowerShell script

echo === Product Search Tool ===
echo Starting the application...
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: PowerShell is not available. Please use the manual setup instructions.
    pause
    exit /b 1
)

echo Running PowerShell script...
powershell -ExecutionPolicy Bypass -File ".\run.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to run PowerShell script.
    echo Please check the error messages above and try running the PowerShell script directly:
    echo powershell -ExecutionPolicy Bypass -File .\run.ps1
    echo.
    echo Or follow the manual setup instructions in WINDOWS_GUIDE.md
    pause
    exit /b 1
)

echo.
echo Application stopped.
pause
