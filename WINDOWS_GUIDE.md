# 🪟 Руководство по установке для Windows

## 📋 Требования

### Обязательные компоненты:
- **Python 3.8+** - [Скачать с python.org](https://www.python.org/downloads/)
- **Node.js 16+** - [Скачать с nodejs.org](https://nodejs.org/)
- **Git** - [Скачать с git-scm.com](https://git-scm.com/)

### Рекомендуемые компоненты:
- **Visual Studio Code** - для редактирования кода
- **Chrome/Edge** - для тестирования

## 🚀 Быстрый запуск

### Вариант 1: Автоматический запуск (Рекомендуется)

1. **Скачайте проект:**
   ```powershell
   git clone https://github.com/your-repo/Product_Search_tool.git
   cd Product_Search_tool
   ```

2. **Запустите автоматический скрипт:**
   ```powershell
   # Откройте PowerShell как администратор
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\run.ps1
   ```

3. **Дождитесь запуска:**
   - Backend API: http://localhost:5001
   - Frontend App: http://localhost:3000

### Вариант 2: Ручная установка

#### Шаг 1: Настройка Backend

1. **Откройте PowerShell в папке backend:**
   ```powershell
   cd backend
   ```

2. **Создайте виртуальное окружение:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Установите зависимости:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Установите Playwright браузеры:**
   ```powershell
   playwright install
   ```

5. **Создайте .env файл:**
   ```powershell
   Copy-Item .env.example .env
   # Отредактируйте .env файл с вашими API ключами
   ```

6. **Запустите backend:**
   ```powershell
   python app.py
   ```

#### Шаг 2: Настройка Frontend

1. **Откройте новое окно PowerShell в папке frontend:**
   ```powershell
   cd frontend
   ```

2. **Установите зависимости:**
   ```powershell
   npm install
   ```

3. **Запустите frontend:**
   ```powershell
   npm start
   ```

## 🔧 Настройка API ключей

### 1. OpenAI API (для AI описаний)
1. Зарегистрируйтесь на [OpenAI](https://platform.openai.com/)
2. Получите API ключ
3. Добавьте в `.env` файл:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 2. 2Captcha API (для решения CAPTCHA)
1. Зарегистрируйтесь на [2Captcha](https://2captcha.com/)
2. Получите API ключ
3. Добавьте в `.env` файл:
   ```
   CAPTCHA_API_KEY=your_2captcha_api_key_here
   ```

### 3. RapidAPI (для AliExpress)
1. Зарегистрируйтесь на [RapidAPI](https://rapidapi.com/)
2. Подпишитесь на AliExpress API
3. Получите API ключ
4. Добавьте в `.env` файл:
   ```
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

## 🐛 Решение проблем

### Проблема: "python не является внутренней или внешней командой"
**Решение:**
1. Убедитесь, что Python установлен
2. Добавьте Python в PATH:
   - Откройте "Система" → "Дополнительные параметры системы" → "Переменные среды"
   - В разделе "Переменные среды пользователя" найдите PATH
   - Добавьте путь к Python (обычно `C:\Users\YourName\AppData\Local\Programs\Python\Python3x\` и `C:\Users\YourName\AppData\Local\Programs\Python\Python3x\Scripts\`)

### Проблема: "npm не является внутренней или внешней командой"
**Решение:**
1. Убедитесь, что Node.js установлен
2. Перезапустите PowerShell после установки Node.js

### Проблема: "Ошибка при активации виртуального окружения"
**Решение:**
```powershell
# Попробуйте альтернативный способ активации
.\venv\Scripts\activate.bat
```

### Проблема: "Ошибка при установке Playwright"
**Решение:**
```powershell
# Установите Playwright вручную
pip install playwright
playwright install
playwright install-deps
```

### Проблема: "CORS ошибка"
**Решение:**
1. Убедитесь, что backend запущен на порту 5001
2. Убедитесь, что frontend запущен на порту 3000
3. Проверьте настройки CORS в `backend/app.py`

### Проблема: "Ошибка при поиске товаров"
**Решение:**
1. Проверьте интернет-соединение
2. Убедитесь, что API ключи настроены правильно
3. Проверьте логи в консоли PowerShell

## 📁 Структура проекта

```
Product_Search_tool/
├── backend/                 # Python Flask API
│   ├── app.py              # Основной файл приложения
│   ├── allegro_enhanced.py # Скрапер Allegro
│   ├── amazon.py           # Скрапер Amazon
│   ├── aliexpress.py       # Скрапер AliExpress
│   ├── requirements.txt    # Python зависимости
│   └── .env.example        # Пример конфигурации
├── frontend/               # React приложение
│   ├── src/                # Исходный код
│   ├── public/             # Статические файлы
│   └── package.json        # Node.js зависимости
├── run.ps1                 # Скрипт запуска для Windows
└── README.md               # Основная документация
```

## 🔄 Обновление приложения

1. **Остановите приложение** (Ctrl+C в PowerShell)
2. **Обновите код:**
   ```powershell
   git pull origin main
   ```
3. **Переустановите зависимости:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   
   cd ../frontend
   npm install
   ```
4. **Запустите заново:**
   ```powershell
   .\run.ps1
   ```

## 📞 Поддержка

Если у вас возникли проблемы:

1. **Проверьте логи** в PowerShell
2. **Убедитесь, что все зависимости установлены**
3. **Проверьте настройки API ключей**
4. **Создайте issue** в репозитории проекта

## 🎯 Готово!

После успешной установки вы сможете:
- ✅ Искать товары на Allegro, Amazon и AliExpress
- ✅ Получать AI-описания товаров
- ✅ Загружать CSV файлы для массового поиска
- ✅ Копировать описания товаров одним кликом

**Приятного использования! 🎉** 