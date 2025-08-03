#!/bin/bash

# =============================================================================
# Скрипт для запуска Google Chrome с remote debugging для Product Search Tool
# =============================================================================

echo "🚀 Запуск Google Chrome с remote debugging для VPN..."

# Определяем операционную систему
OS="$(uname -s)"
CHROME_PATH=""
USER_DATA_DIR=""

case "${OS}" in
    Darwin*)    # macOS
        CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        USER_DATA_DIR="$HOME/Library/Application Support/Google/Chrome-Debug"
        ;;
    Linux*)     # Linux
        if [ -f "/usr/bin/google-chrome" ]; then
            CHROME_PATH="/usr/bin/google-chrome"
        elif [ -f "/usr/bin/google-chrome-stable" ]; then
            CHROME_PATH="/usr/bin/google-chrome-stable"
        else
            echo "❌ Google Chrome не найден в системе"
            exit 1
        fi
        USER_DATA_DIR="$HOME/.config/google-chrome-debug"
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)    # Windows
        CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe"
        if [ ! -f "$CHROME_PATH" ]; then
            CHROME_PATH="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        fi
        USER_DATA_DIR="$HOME/AppData/Local/Google/Chrome-Debug"
        ;;
    *)
        echo "❌ Неподдерживаемая операционная система: ${OS}"
        exit 1
        ;;
esac

# Проверяем, существует ли Chrome
if [ ! -f "$CHROME_PATH" ]; then
    echo "❌ Google Chrome не найден по пути: $CHROME_PATH"
    echo "💡 Установите Google Chrome или укажите правильный путь в переменной CHROME_EXECUTABLE_PATH"
    exit 1
fi

# Создаем директорию для пользовательских данных
mkdir -p "$USER_DATA_DIR"

# Порт для remote debugging
DEBUG_PORT=9222

echo "📍 Путь к Chrome: $CHROME_PATH"
echo "📁 Директория данных: $USER_DATA_DIR"
echo "🔌 Порт debugging: $DEBUG_PORT"

# Проверяем, не занят ли порт
if lsof -Pi :$DEBUG_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ Порт $DEBUG_PORT уже используется"
    echo "💡 Возможно, Chrome уже запущен с remote debugging"
    echo "💡 Или завершите процесс: lsof -ti:$DEBUG_PORT | xargs kill -9"
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🌐 Запускаем Chrome с remote debugging..."
echo "💡 После запуска настройте VPN в Chrome и оставьте браузер открытым"
echo "💡 Затем запустите поиск в Product Search Tool"
echo ""

# Запускаем Chrome с необходимыми флагами
"$CHROME_PATH" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --disable-web-security \
    --disable-features=VizDisplayCompositor \
    --disable-blink-features=AutomationControlled \
    --no-first-run \
    --no-default-browser-check \
    --disable-default-apps \
    --disable-popup-blocking \
    --disable-translate \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    --disable-client-side-phishing-detection \
    --disable-sync \
    --metrics-recording-only \
    --no-report-upload \
    --disable-domain-reliability \
    --disable-component-update &

CHROME_PID=$!

echo "✅ Chrome запущен с PID: $CHROME_PID"
echo "🔌 Remote debugging доступен на: http://localhost:$DEBUG_PORT"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте VPN в открывшемся Chrome"
echo "2. В файле .env установите:"
echo "   CONNECT_TO_EXISTING_CHROME=true"
echo "   USE_INSTALLED_CHROME=true"
echo "3. Запустите Product Search Tool"
echo ""
echo "🛑 Для остановки нажмите Ctrl+C"

# Ожидаем сигнал завершения
trap "echo '🛑 Останавливаем Chrome...'; kill $CHROME_PID 2>/dev/null; exit" INT

# Ждем завершения процесса Chrome
wait $CHROME_PID
