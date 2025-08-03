#!/bin/bash

# =============================================================================
# Скрипт для быстрой настройки Chrome с VPN для Product Search Tool
# =============================================================================

echo "🔧 Настройка Chrome с VPN для Product Search Tool"
echo "=================================================="

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    echo "📝 Создаем .env файл из шаблона..."
    cp .env.example .env
    echo "✅ Файл .env создан"
else
    echo "📝 Файл .env уже существует"
fi

# Функция для обновления переменной в .env
update_env_var() {
    local var_name=$1
    local var_value=$2
    local env_file=".env"
    
    if grep -q "^${var_name}=" "$env_file"; then
        # Переменная существует, обновляем
        sed -i.bak "s/^${var_name}=.*/${var_name}=${var_value}/" "$env_file"
    else
        # Переменная не существует, добавляем
        echo "${var_name}=${var_value}" >> "$env_file"
    fi
}

echo ""
echo "🌐 Настройка Chrome для использования с VPN..."

# Настраиваем использование установленного Chrome
update_env_var "USE_INSTALLED_CHROME" "true"
update_env_var "CONNECT_TO_EXISTING_CHROME" "false"
update_env_var "CHROME_DEBUG_PORT" "9222"

echo "✅ Настройки Chrome обновлены в .env файле"

# Определяем путь к Chrome для текущей ОС
OS="$(uname -s)"
case "${OS}" in
    Darwin*)    # macOS
        CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ;;
    Linux*)     # Linux
        if [ -f "/usr/bin/google-chrome" ]; then
            CHROME_PATH="/usr/bin/google-chrome"
        elif [ -f "/usr/bin/google-chrome-stable" ]; then
            CHROME_PATH="/usr/bin/google-chrome-stable"
        fi
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)    # Windows
        CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if [ ! -f "$CHROME_PATH" ]; then
            CHROME_PATH="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        fi
        ;;
esac

if [ -n "$CHROME_PATH" ] && [ -f "$CHROME_PATH" ]; then
    echo "🔍 Найден Chrome: $CHROME_PATH"
    update_env_var "CHROME_EXECUTABLE_PATH" "$CHROME_PATH"
    echo "✅ Путь к Chrome сохранен в .env"
else
    echo "⚠️ Chrome не найден автоматически"
    echo "💡 Укажите путь вручную в .env файле: CHROME_EXECUTABLE_PATH="
fi

echo ""
echo "📋 Варианты использования:"
echo ""
echo "🔹 Вариант 1 (Рекомендуется): Автоматический запуск Chrome"
echo "   - Просто запустите приложение: ./run.sh"
echo "   - Chrome запустится автоматически с вашими VPN настройками"
echo ""
echo "🔹 Вариант 2: Подключение к уже запущенному Chrome"
echo "   1. Запустите Chrome с VPN: ./start_chrome_with_vpn.sh"
echo "   2. Настройте VPN в открывшемся Chrome"
echo "   3. В .env установите: CONNECT_TO_EXISTING_CHROME=true"
echo "   4. Запустите приложение: ./run.sh"
echo ""
echo "✅ Настройка завершена!"
echo "💡 Теперь Allegro будет использовать ваш Chrome с VPN"
