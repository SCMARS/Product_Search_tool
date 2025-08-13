# Windows Guide - Product Search Tool

## 🚀 Быстрый старт для Windows

### Предварительные требования

1. **Python 3.8+**
   - Скачайте с [python.org](https://www.python.org/downloads/)
   - Убедитесь, что отмечена опция "Add Python to PATH" при установке

2. **Node.js 16+**
   - Скачайте с [nodejs.org](https://nodejs.org/)
   - Рекомендуется LTS версия

3. **Git** (опционально)
   - Скачайте с [git-scm.com](https://git-scm.com/)

### 🎯 Автоматический запуск

#### Вариант 1: Batch файл (рекомендуется)
```cmd
# Двойной клик на файл или запуск из командной строки
start_app.bat
```

#### Вариант 2: PowerShell скрипт
```powershell
# Запуск PowerShell от имени администратора
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\run.ps1
```

### 🔧 Ручная установка

#### 1. Клонирование репозитория
```cmd
git clone <repository-url>
cd Product_Search_tool
```

#### 2. Настройка Backend
```cmd
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
venv\Scripts\activate.bat

# Установка зависимостей
pip install -r requirements.txt

# Установка Playwright браузеров
playwright install

# Создание .env файла (если не существует)
copy .env.example .env
```

#### 3. Настройка Frontend
```cmd
cd frontend

# Установка зависимостей
npm install
```

#### 4. Запуск приложения

**Backend (в отдельном окне):**
```cmd
cd backend
venv\Scripts\activate.bat
python app.py
```

**Frontend (в отдельном окне):**
```cmd
cd frontend
npm start
```

### 🌐 Доступ к приложению

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5003
- **Health Check:** http://localhost:5003/health

### 🐳 Docker (альтернативный способ)

#### Установка Docker Desktop
1. Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Установите и перезагрузите компьютер
3. Запустите Docker Desktop

#### Запуск с Docker
```cmd
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d
```

### 🔍 Проверка работоспособности

#### 1. Проверка Backend
```cmd
curl http://localhost:5003/health
```
Ожидаемый ответ:
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "version": "1.0.0",
  "services": {
    "flask": "running",
    "playwright": "available"
  }
}
```

#### 2. Проверка Frontend
Откройте http://localhost:3000 в браузере

### 🛠️ Устранение неполадок

#### Проблема: Python не найден
```cmd
# Проверьте версию Python
python --version

# Если не работает, попробуйте
python3 --version
```

#### Проблема: npm не найден
```cmd
# Проверьте версию Node.js
node --version
npm --version
```

#### Проблема: Порт занят
```cmd
# Проверьте, какие процессы используют порты
netstat -ano | findstr :5003
netstat -ano | findstr :3000

# Остановите процесс по PID
taskkill /f /pid <PID>
```

#### Проблема: Виртуальное окружение не активируется
```cmd
# Убедитесь, что вы в правильной директории
cd backend

# Проверьте наличие venv
dir venv\Scripts

# Активируйте вручную
venv\Scripts\activate.bat
```

#### Проблема: Зависимости не устанавливаются
```cmd
# Обновите pip
python -m pip install --upgrade pip

# Установите зависимости снова
pip install -r requirements.txt
```

### 📁 Структура проекта

```
Product_Search_tool/
├── backend/                 # Python Flask backend
│   ├── app.py              # Основное приложение
│   ├── requirements.txt    # Python зависимости
│   ├── venv/              # Виртуальное окружение
│   └── .env               # Переменные окружения
├── frontend/               # React frontend
│   ├── src/               # Исходный код
│   ├── package.json       # Node.js зависимости
│   └── node_modules/      # Установленные модули
├── start_app.bat          # Windows batch скрипт
├── run.ps1                # PowerShell скрипт
└── docker-compose.yml     # Docker конфигурация
```

### 🔐 Настройка API ключей

1. Создайте файл `backend/.env`:
```env
FLASK_ENV=development
PORT=5003
PYTHONUNBUFFERED=1

# API Keys (опционально)
OPENAI_API_KEY=your_openai_api_key_here
CAPTCHA_API_KEY=your_2captcha_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

### 📝 Логи

#### Backend логи
- Логи Flask: `backend/logs/`
- Временные файлы: `backend/temp/`

#### Frontend логи
- Логи React: в консоли браузера (F12)
- Логи npm: в терминале

### 🚀 Производительность

#### Оптимизация для Windows
1. **Отключите антивирус** для папки проекта (временно)
2. **Используйте SSD** для лучшей производительности
3. **Увеличьте память** для Docker (если используется)

#### Мониторинг ресурсов
```cmd
# Мониторинг CPU и памяти
taskmgr

# Мониторинг сети
netstat -e
```

### 🔄 Обновление

#### Обновление кода
```cmd
# Остановите приложение
# Обновите код из репозитория
git pull

# Переустановите зависимости
cd backend
venv\Scripts\activate.bat
pip install -r requirements.txt

cd ../frontend
npm install
```

### 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в консоли
2. Убедитесь, что все порты свободны
3. Проверьте версии Python и Node.js
4. Обратитесь к разделу "Устранение неполадок"

### 🎯 Готово!

Ваше приложение готово к использованию! Откройте http://localhost:3000 в браузере для начала работы. 