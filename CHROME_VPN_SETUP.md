# 🌐 Настройка Chrome с VPN для Product Search Tool

## 🚀 Быстрый старт

### Вариант 1: Автоматическая настройка (Рекомендуется)

```bash
# 1. Настройка
./setup_chrome_vpn.sh

# 2. Запуск
./run.sh
```

После этого приложение будет автоматически использовать ваш Google Chrome с настройками VPN.

### Вариант 2: Подключение к уже запущенному Chrome

```bash
# 1. Запуск Chrome с remote debugging
./start_chrome_with_vpn.sh

# 2. Настройте VPN в открывшемся Chrome

# 3. В файле .env установите:
# CONNECT_TO_EXISTING_CHROME=true

# 4. Запуск приложения
./run.sh
```

## 🔧 Ручная настройка

### 1. Создайте .env файл
```bash
cp .env.example .env
```

### 2. Настройте переменные в .env:
```env
# Основные настройки Chrome
USE_INSTALLED_CHROME=true
CONNECT_TO_EXISTING_CHROME=false
CHROME_DEBUG_PORT=9222

# Путь к Chrome (автоопределение если пусто)
CHROME_EXECUTABLE_PATH=

# Для macOS:
# CHROME_EXECUTABLE_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome

# Для Linux:
# CHROME_EXECUTABLE_PATH=/usr/bin/google-chrome

# Для Windows:
# CHROME_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
```

## 🧪 Тестирование

Проверьте настройки перед запуском:

```bash
python3 test_chrome_vpn.py
```

Этот скрипт:
- Проверит подключение к Chrome
- Покажет ваш IP адрес
- Проверит доступность Allegro.pl

## ❓ Решение проблем

### Chrome не найден
```bash
# Проверьте, установлен ли Chrome
which google-chrome
# или для macOS
ls "/Applications/Google Chrome.app"

# Укажите путь вручную в .env:
CHROME_EXECUTABLE_PATH=/path/to/your/chrome
```

### Не удается подключиться к запущенному Chrome
```bash
# Убедитесь, что Chrome запущен с правильными флагами:
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug

# Проверьте, что порт доступен:
curl http://localhost:9222/json/version
```

### VPN не работает
1. Убедитесь, что VPN настроен в Chrome
2. Проверьте IP через: https://whatismyipaddress.com/
3. Убедитесь, что Chrome использует правильный профиль с VPN

## 💡 Полезные советы

1. **Для стабильной работы** используйте отдельный профиль Chrome для парсинга
2. **Настройте VPN** перед запуском приложения
3. **Не закрывайте Chrome** во время работы приложения
4. **Используйте качественный VPN** с серверами в Польше для Allegro.pl

## 🔍 Проверка работы

После настройки:
1. Запустите приложение: `./run.sh`
2. Откройте http://localhost:3000
3. Попробуйте поиск товара на Allegro
4. В логах должно появиться: "✅ Используем установленный Chrome" или "✅ Подключились к запущенному Chrome"
