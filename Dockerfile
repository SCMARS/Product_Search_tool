# Multi-stage build для оптимизации размера
FROM node:18-alpine AS frontend-build

# Устанавливаем рабочую директорию для frontend
WORKDIR /app/frontend

# Копируем package.json и package-lock.json
COPY frontend/package*.json ./

# Устанавливаем зависимости
RUN npm ci --only=production

# Копируем исходный код frontend
COPY frontend/ ./

# Собираем production build
RUN npm run build

# Backend stage
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Playwright и браузеры
RUN pip install playwright==1.40.0
RUN playwright install chromium
RUN playwright install-deps chromium

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY backend/requirements.txt ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем backend код
COPY backend/ ./

# Копируем собранный frontend
COPY --from=frontend-build /app/frontend/build ./static

# Создаем директории для uploads и logs
RUN mkdir -p uploads logs

# Устанавливаем переменные окружения
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Открываем порт
EXPOSE 5003

# Команда запуска
CMD ["python", "app.py"]
