#!/bin/bash

# Скрипт для запуска приложения на macOS
echo "🚀 Запуск Product Search Tool на macOS..."

# Проверяем, существует ли виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

# Запускаем приложение
echo "🎯 Запуск Flask приложения..."
python app.py 