# 🚀 Product Search Tool - Руководство по деплою

Полное руководство по развертыванию Product Search Tool с использованием Docker.

## 📋 Требования

### Системные требования
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Минимум 4GB RAM** (рекомендуется 8GB)
- **Минимум 10GB свободного места**

### API ключи
- **2Captcha API Key** - для решения CAPTCHA (получить на [2captcha.com](https://2captcha.com/))
- **OpenAI API Key** - для генерации изображений (получить на [platform.openai.com](https://platform.openai.com/))

## 🛠️ Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone <repository-url>
cd Product_search_tool_e_finder

# Создаем файл переменных окружения
cp .env.example .env

# Редактируем .env файл
nano .env
```

### 2. Настройка переменных окружения

Отредактируйте файл `.env`:

```env
# API ключи (ОБЯЗАТЕЛЬНО)
CAPTCHA_API_KEY=your_2captcha_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Остальные настройки можно оставить по умолчанию
FLASK_ENV=production
```

### 3. Запуск

#### Автоматический деплой (рекомендуется)
```bash
./deploy.sh
```

#### Ручной деплой
```bash
# Разработка
make install

# Или продакшен
make deploy-prod
```

## 🎯 Доступные команды

### Make команды

```bash
make help           # Показать все доступные команды
make install        # Первоначальная установка
make up             # Запустить в режиме разработки
make prod           # Запустить в режиме продакшена
make down           # Остановить все сервисы
make logs           # Показать логи
make health         # Проверить статус сервисов
make clean          # Очистить все Docker ресурсы
```

### Docker Compose команды

```bash
# Разработка
docker-compose up -d
docker-compose logs -f
docker-compose down

# Продакшен
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
```

## 🌐 Доступ к сервисам

После успешного запуска:

- **Frontend**: http://localhost (порт 80)
- **Backend API**: http://localhost:5001
- **Health Check**: http://localhost:5001/health
- **Redis** (внутренний): localhost:6379

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус контейнеров
docker-compose ps

# Health check
curl http://localhost:5001/health

# Логи в реальном времени
make logs
```

### Основные метрики
```bash
# Использование ресурсов
docker stats

# Логи конкретного сервиса
make logs-backend
make logs-frontend
```

## 🔧 Отладка

### Частые проблемы

#### 1. Контейнер не запускается
```bash
# Проверяем логи
docker-compose logs backend
docker-compose logs frontend

# Проверяем образы
docker images

# Пересобираем образы
docker-compose build --no-cache
```

#### 2. API ключи не работают
```bash
# Проверяем переменные окружения
docker-compose exec backend env | grep API

# Проверяем .env файл
cat .env
```

#### 3. Playwright не работает
```bash
# Входим в контейнер backend
docker-compose exec backend /bin/bash

# Проверяем браузеры
playwright install --dry-run
```

#### 4. Проблемы с CAPTCHA
```bash
# Проверяем логи backend
docker-compose logs -f backend | grep CAPTCHA

# Тестируем 2Captcha API
curl -X POST "https://2captcha.com/in.php" \
  -d "key=YOUR_API_KEY" \
  -d "method=userrecaptcha" \
  -d "googlekey=test" \
  -d "pageurl=https://example.com"
```

### Вход в контейнеры
```bash
# Backend
make shell-backend
# или
docker-compose exec backend /bin/bash

# Frontend
make shell-frontend
# или
docker-compose exec frontend /bin/sh
```

## 🏭 Продакшен

### Дополнительные настройки для продакшена

1. **SSL сертификаты**
```bash
# Создайте директорию для SSL
mkdir -p nginx/ssl

# Добавьте ваши сертификаты
cp your-cert.pem nginx/ssl/
cp your-key.pem nginx/ssl/
```

2. **Настройка домена**
Отредактируйте `frontend/nginx.conf`:
```nginx
server_name your-domain.com;
```

3. **Масштабирование**
```bash
# Запуск нескольких экземпляров backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Мониторинг в продакшене

1. **Логирование**
```bash
# Настройка ротации логов
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
systemctl restart docker
```

2. **Backup**
```bash
# Backup данных Redis
docker-compose exec redis redis-cli BGSAVE

# Backup логов
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## 🔄 Обновление

### Обновление кода
```bash
# Получаем последние изменения
git pull origin main

# Пересобираем и перезапускаем
make deploy
```

### Обновление зависимостей
```bash
# Обновляем Python зависимости
docker-compose exec backend pip install -r requirements.txt --upgrade

# Обновляем Node.js зависимости
docker-compose exec frontend npm update
```

## 📈 Производительность

### Оптимизация

1. **Ограничение ресурсов**
```yaml
# В docker-compose.prod.yml уже настроено
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

2. **Кэширование**
- Redis используется для кэширования результатов
- Nginx кэширует статические файлы

3. **Мониторинг производительности**
```bash
# Использование ресурсов
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Время ответа API
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5001/health
```

## 🆘 Поддержка

### Сбор информации для отладки
```bash
# Создаем отчет о системе
./debug-info.sh > debug-report.txt
```

### Полезные ссылки
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [2Captcha API Documentation](https://2captcha.com/2captcha-api)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 📝 Changelog

### v1.0.0
- Первый релиз с Docker поддержкой
- Поддержка Allegro, Amazon, AliExpress
- Автоматическое решение CAPTCHA
- Веб-интерфейс на React
