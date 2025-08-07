#!/bin/bash

echo "=== Product Search Tool ==="
echo "Starting the application..."

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "flask run" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

# Wait a moment
sleep 2

# Start backend
echo "Starting backend..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start frontend
echo "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 10

echo ""
echo "=== Application is running! ==="
echo "Backend: http://localhost:5001"
echo "Frontend: http://localhost:3000"
echo ""
echo "Open http://localhost:3000 in your browser"
echo ""
echo "Press Ctrl+C to stop the application"

# Wait for user to stop
trap "echo 'Stopping application...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 