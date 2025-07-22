#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check for required commands
# Check for Python (either python or python3)
PYTHON_CMD="python"
if ! command_exists python; then
  if command_exists python3; then
    PYTHON_CMD="python3"
  else
    echo "Error: Python is not installed. Please install Python 3.6 or higher."
    exit 1
  fi
fi

if ! command_exists npm; then
  echo "Error: npm is not installed. Please install Node.js and npm."
  exit 1
fi

# Print welcome message
echo "=== Product Search Tool ==="
echo "Starting the application..."
echo

# Setup and run backend
echo "Setting up backend..."
cd backend || { echo "Error: backend directory not found"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Start Flask server in the background
echo "Starting Flask server..."
flask run --port=5001 &
FLASK_PID=$!

# Wait for Flask to start
echo "Waiting for Flask server to start..."
sleep 3

# Setup and run frontend
echo
echo "Setting up frontend..."
cd ../frontend || { echo "Error: frontend directory not found"; exit 1; }

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# Start React development server
echo "Starting React development server..."
npm start &
REACT_PID=$!

# Wait for user to press Ctrl+C
echo
echo "Application is running!"
echo "- Backend: http://localhost:5001"
echo "- Frontend: http://localhost:3000"
echo
echo "Press Ctrl+C to stop the application"

# Handle Ctrl+C
trap "echo 'Stopping application...'; kill $FLASK_PID $REACT_PID 2>/dev/null; exit" INT

# Wait for processes to finish
wait
