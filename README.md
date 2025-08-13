# Product Search Tool

Инструмент для поиска товаров на Allegro, Amazon и AliExpress с поддержкой AI-описаний и генерации изображений.

## 🚀 Быстрый старт

### Требования
- Python 3.8+ (на macOS используйте команды с `python3`)
- Node.js 16+
- Git

### Вариант A. Автозапуск (Windows)
- Запустите `start_app.bat` двойным кликом
- Либо PowerShell: разрешите запуск и выполните `./run.ps1`

### Вариант B. Ручной запуск (кроссплатформенно)

1) Backend
```bash
cd backend

# Создание виртуального окружения
# Windows:
python -m venv venv
# macOS/Linux:
python3 -m venv venv

# Активация окружения
# Windows:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# (опционально) Установка браузеров Playwright
playwright install || true

# Запуск backend
# Windows:
python app.py
# macOS/Linux:
python3 app.py
```

2) Frontend (в новом окне/вкладке терминала)
```bash
cd frontend
npm install
npm start
```

### Доступ
- Frontend: http://localhost:3000
- Backend API: http://localhost:5003
- Health: http://localhost:5003/health

## 🔐 Переменные окружения
Создайте файл `backend/.env` (можно скопировать из `backend/env.example`) и при необходимости добавьте ключи:
```env
FLASK_ENV=development
PORT=5003
PYTHONUNBUFFERED=1

# Опционально
OPENAI_API_KEY=your_openai_api_key_here
CAPTCHA_API_KEY=your_2captcha_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

## ✅ Проверка
```bash
# Проверка бэкенда
curl http://localhost:5003/health
# Откройте фронтенд в браузере:
# http://localhost:3000
```

## ⚠️ Известные моменты
- Amazon может периодически возвращать 503 (Service Unavailable). Это связано с защитами и нагрузкой.
  - Что делать: подождать 10–30 минут; использовать Allegro/AliExpress; при желании использовать VPN/прокси; снизить частоту запросов.
- Если видите в UI «Network error. Check CORS configuration on server.» — почти всегда не запущен backend или он на другом порту.
  - Проверьте: `curl http://localhost:5003/health` должен вернуть JSON со статусом `healthy`.

## 🛠️ Траблшутинг
- Python не найден на macOS: используйте `python3` / `python3 -m venv venv`.
- Порты заняты:
  - macOS/Linux: `lsof -ti:5003 | xargs kill -9` и `lsof -ti:3000 | xargs kill -9`
  - Windows: `netstat -ano | findstr :5003` и `taskkill /f /pid <PID>`
- Ошибки установки `pandas`/зависимостей: убедитесь, что используете актуальный Python (3.8+) и версии из `backend/requirements.txt`.

## 🐳 Docker (опционально)
```bash
docker-compose up --build
# или в фоне
docker-compose up -d
```

## Структура
```
Product_Search_tool/
├── backend/              # Flask API
│   ├── app.py
│   ├── requirements.txt
│   └── env.example
├── frontend/             # React UI
├── start_app.bat         # Автозапуск на Windows
├── run.ps1               # Автозапуск на Windows (PowerShell)
├── docker-compose.yml
└── README.md
```