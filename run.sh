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
    echo "ℹ️  Используем python3 вместо python"
  else
    echo "❌ Ошибка: Python не установлен. Установите Python 3.6 или выше."
    exit 1
  fi
fi

if ! command_exists npm; then
  echo "❌ Ошибка: npm не установлен. Установите Node.js и npm."
  exit 1
fi

# Print welcome message
echo "=== Product Search Tool ==="
echo "🚀 Запуск приложения..."
echo

# Setup and run backend
echo "🔧 Настройка backend..."
cd backend || { echo "❌ Ошибка: директория backend не найдена"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "📦 Создание виртуального окружения..."
  $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate || { echo "❌ Ошибка: Не удалось активировать виртуальное окружение"; exit 1; }

# Install dependencies
echo "📥 Установка зависимостей backend..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Установка браузеров Playwright..."
playwright install

# Start Flask server in the background
echo "🎯 Запуск Flask сервера..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
echo "⏳ Ожидание запуска Flask сервера..."
sleep 3

# Setup and run frontend
echo
echo "🔧 Настройка frontend..."
cd ../frontend || { echo "❌ Ошибка: директория frontend не найдена"; exit 1; }

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  echo "📥 Установка зависимостей frontend..."
  npm install
fi

# Start React development server
echo "🎯 Запуск React development сервера..."
npm start &
REACT_PID=$!

# Wait for user to press Ctrl+C
echo
echo "✅ Приложение запущено!"
echo "- Backend: http://localhost:5001"
echo "- Frontend: http://localhost:3000"
echo
echo "Нажмите Ctrl+C для остановки приложения"

# Handle Ctrl+C
trap "echo '🛑 Остановка приложения...'; kill $FLASK_PID $REACT_PID 2>/dev/null; exit" INT

# Wait for processes to finish
wait
