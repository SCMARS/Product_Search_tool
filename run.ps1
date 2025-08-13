# Product Search Tool - Windows PowerShell Startup Script

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to stop background processes
function Stop-BackgroundProcesses {
    Write-Host "Stopping background processes..."
    
    # Stop Flask processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*flask*" -or $_.CommandLine -like "*app.py*" } | Stop-Process -Force
    
    # Stop Node.js processes
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*npm*start*" } | Stop-Process -Force
    
    Write-Host "Background processes stopped."
}

# Set up Ctrl+C handler
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Stop-BackgroundProcesses
}

# Check for required commands
# Check for Python (either python or python3)
$PYTHON_CMD = "python"
if (-not (Test-CommandExists $PYTHON_CMD)) {
    if (Test-CommandExists "python3") {
        $PYTHON_CMD = "python3"
    } else {
        Write-Host "Error: Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
        Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

if (-not (Test-CommandExists "npm")) {
    Write-Host "Error: npm is not installed. Please install Node.js and npm." -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Print welcome message
Write-Host "=== Product Search Tool ===" -ForegroundColor Green
Write-Host "Starting the application..." -ForegroundColor Cyan
Write-Host ""

# Get the original location to return to
$originalLocation = Get-Location

try {
    # Setup and run backend
    Write-Host "Setting up backend..." -ForegroundColor Yellow
    Set-Location -Path "backend" -ErrorAction Stop

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path -Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        & $PYTHON_CMD -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to create virtual environment." -ForegroundColor Red
            exit 1
        }
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    $activateScript = ".\venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to activate virtual environment." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Error: Failed to activate virtual environment. Activation script not found at $activateScript" -ForegroundColor Red
        exit 1
    }

    # Install dependencies
    Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Some dependencies may not have installed correctly." -ForegroundColor Yellow
    }

    # Install Playwright browsers
    Write-Host "Installing Playwright browsers..." -ForegroundColor Cyan
    playwright install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Failed to install Playwright browsers. Some features may not work." -ForegroundColor Yellow
    }

    # Check if .env file exists, if not create from example
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Write-Host "Creating .env file from example..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
    }

    # Start backend
    Write-Host "Starting backend server..." -ForegroundColor Green
    Start-Process -FilePath "cmd" -ArgumentList "/k", "venv\Scripts\activate.bat && python app.py" -WindowStyle Normal
    $backendProcess = $true

    # Wait for backend to start
    Write-Host "Waiting for backend to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 8

    # Check if backend is running
    Write-Host "Checking if backend is running..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5003/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is running successfully!" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Backend may not be running properly. Status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ Backend may not be running properly. Please check the backend window for errors." -ForegroundColor Yellow
    }

    # Setup and run frontend
    Write-Host "Setting up frontend..." -ForegroundColor Yellow
    Set-Location -Path "..\frontend" -ErrorAction Stop

    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to install frontend dependencies." -ForegroundColor Red
            exit 1
        }
    }

    # Start frontend
    Write-Host "Starting frontend server..." -ForegroundColor Green
    Start-Process -FilePath "cmd" -ArgumentList "/k", "npm start" -WindowStyle Normal
    $frontendProcess = $true

    # Wait for frontend to start
    Write-Host "Waiting for frontend to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10

    # Return to original location
    Set-Location -Path $originalLocation

    # Success message
    Write-Host ""
    Write-Host "=== Application is running! ===" -ForegroundColor Green
    Write-Host "- Backend API: http://localhost:5003" -ForegroundColor Cyan
    Write-Host "- Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Open http://localhost:3000 in your browser" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the application..." -ForegroundColor Yellow

    # Keep the script running
    while ($true) {
        Start-Sleep -Seconds 1
    }

} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "Stopping application..." -ForegroundColor Yellow
    Stop-BackgroundProcesses
    Set-Location -Path $originalLocation
}
