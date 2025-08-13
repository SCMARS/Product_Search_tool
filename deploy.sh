#!/bin/bash

# Скрипт для деплоя Product Search Tool

set -e  # Остановить выполнение при ошибке

echo "🚀 Начинаем деплой Product Search Tool..."

# Проверяем, что Docker установлен
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаем из примера..."
    cp .env.example .env
    echo "📝 Отредактируйте файл .env и добавьте ваши API ключи:"
    echo "   - CAPTCHA_API_KEY (получить на https://2captcha.com/)"
    echo "   - OPENAI_API_KEY (получить на https://platform.openai.com/)"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
fi

# Выбираем режим деплоя
echo "Выберите режим деплоя:"
echo "1. Разработка (development)"
echo "2. Продакшен (production)"
read -p "Введите номер (1-2): " deploy_mode

case $deploy_mode in
    1)
        echo "🔧 Запускаем в режиме разработки..."
        COMPOSE_FILE="docker-compose.yml"
        ;;
    2)
        echo "🏭 Запускаем в режиме продакшена..."
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    *)
        echo "❌ Неверный выбор. Используем режим разработки."
        COMPOSE_FILE="docker-compose.yml"
        ;;
esac

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Собираем образы
echo "🔨 Собираем Docker образы..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Запускаем контейнеры
echo "▶️  Запускаем контейнеры..."
docker-compose -f $COMPOSE_FILE up -d

# Ждем запуска сервисов
echo "⏳ Ждем запуска сервисов..."
sleep 30

# Проверяем статус сервисов
echo "🔍 Проверяем статус сервисов..."
docker-compose -f $COMPOSE_FILE ps

# Проверяем health check
echo "🏥 Проверяем health check..."
if curl -f http://localhost:5003/health > /dev/null 2>&1; then
    echo "✅ Backend запущен успешно"
else
    echo "❌ Backend не отвечает"
fi

if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "✅ Frontend запущен успешно"
else
    echo "❌ Frontend не отвечает"
fi

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📱 Доступные сервисы:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost:5003"
echo "   Health Check: http://localhost:5003/health"
echo ""
echo "📋 Полезные команды:"
echo "   Просмотр логов: docker-compose -f $COMPOSE_FILE logs -f"
echo "   Остановка: docker-compose -f $COMPOSE_FILE down"
echo "   Перезапуск: docker-compose -f $COMPOSE_FILE restart"
echo ""
echo "🔧 Для отладки:"
echo "   Backend логи: docker-compose -f $COMPOSE_FILE logs -f backend"
echo "   Frontend логи: docker-compose -f $COMPOSE_FILE logs -f frontend"
