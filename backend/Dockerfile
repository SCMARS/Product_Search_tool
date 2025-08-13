# Backend Dockerfile
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
COPY requirements.txt ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем backend код
COPY . .

# Создаем директории для uploads и logs
RUN mkdir -p uploads logs temp

# Устанавливаем переменные окружения
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PORT=5003
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 5003

# Команда запуска
CMD ["python", "app.py"] 