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
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*flask*" } | Stop-Process -Force
    
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
        Write-Host "Error: Python is not installed. Please install Python 3.6 or higher." -ForegroundColor Red
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
        Write-Host "Error: Failed to install backend dependencies." -ForegroundColor Red
        exit 1
    }

    # Install Playwright browsers
    Write-Host "Installing Playwright browsers..." -ForegroundColor Cyan
    playwright install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Failed to install Playwright browsers. Some features may not work." -ForegroundColor Yellow
    }

    # Check if .env file exists, if not create from example
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Write-Host "Creating .env file from .env.example..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
        Write-Host "Please edit .env file with your API credentials." -ForegroundColor Yellow
    }

    # Start Flask server in the background
    Write-Host "Starting Flask server..." -ForegroundColor Cyan
    $env:FLASK_APP = "app.py"
    $flaskProcess = Start-Process -FilePath $PYTHON_CMD -ArgumentList "app.py" -PassThru -WindowStyle Hidden
    
    if (-not $flaskProcess) {
        Write-Host "Error: Failed to start Flask server." -ForegroundColor Red
        exit 1
    }

    # Wait for Flask to start
    Write-Host "Waiting for Flask server to start..." -ForegroundColor Cyan
    $maxAttempts = 10
    $attempt = 0
    $flaskReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $flaskReady) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5001" -TimeoutSec 5 -ErrorAction SilentlyContinue
            $flaskReady = $true
            Write-Host "Flask server is ready!" -ForegroundColor Green
        } catch {
            $attempt++
            Write-Host "Waiting for Flask server... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        }
    }

    if (-not $flaskReady) {
        Write-Host "Warning: Flask server may not be ready yet, but continuing..." -ForegroundColor Yellow
    }

    # Setup and run frontend
    Write-Host ""
    Write-Host "Setting up frontend..." -ForegroundColor Yellow
    Set-Location -Path "..\frontend" -ErrorAction Stop

    # Install dependencies if node_modules doesn't exist
    if (-not (Test-Path -Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to install frontend dependencies." -ForegroundColor Red
            exit 1
        }
    }

    # Start React development server
    Write-Host "Starting React development server..." -ForegroundColor Cyan
    $reactProcess = Start-Process -FilePath "npm" -ArgumentList "start" -PassThru -WindowStyle Hidden

    if (-not $reactProcess) {
        Write-Host "Error: Failed to start React development server." -ForegroundColor Red
        exit 1
    }

    # Wait for React to start
    Write-Host "Waiting for React development server to start..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5

    # Display information
    Write-Host ""
    Write-Host "Application is running!" -ForegroundColor Green
    Write-Host "- Backend API: http://localhost:5001" -ForegroundColor Cyan
    Write-Host "- Frontend App: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The application should open automatically in your browser." -ForegroundColor Yellow
    Write-Host "If not, please open http://localhost:3000 manually." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Magenta

    # Keep the script running until user presses Ctrl+C
    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    } catch [System.Management.Automation.PipelineStoppedException] {
        # This is expected when Ctrl+C is pressed
        Write-Host ""
        Write-Host "Shutting down..." -ForegroundColor Yellow
    }

} catch {
    Write-Host "An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Return to original location
    Set-Location $originalLocation
    
    # Stop background processes
    Stop-BackgroundProcesses
    
    Write-Host "Application stopped." -ForegroundColor Green
}
