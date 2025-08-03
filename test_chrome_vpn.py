#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Chrome с VPN
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем backend в путь
sys.path.append('backend')

# Загружаем переменные окружения
load_dotenv()

async def test_chrome_connection():
    """Тестирует подключение к Chrome и проверяет IP"""
    
    try:
        from playwright.async_api import async_playwright
        
        print("🧪 Тестируем подключение к Chrome с VPN...")
        print("=" * 50)
        
        # Проверяем настройки
        use_installed_chrome = os.getenv('USE_INSTALLED_CHROME', 'true').lower() == 'true'
        connect_to_existing = os.getenv('CONNECT_TO_EXISTING_CHROME', 'false').lower() == 'true'
        chrome_path = os.getenv('CHROME_EXECUTABLE_PATH', '')
        debug_port = os.getenv('CHROME_DEBUG_PORT', '9222')
        
        print(f"📋 Настройки:")
        print(f"   USE_INSTALLED_CHROME: {use_installed_chrome}")
        print(f"   CONNECT_TO_EXISTING_CHROME: {connect_to_existing}")
        print(f"   CHROME_EXECUTABLE_PATH: {chrome_path or 'автопоиск'}")
        print(f"   CHROME_DEBUG_PORT: {debug_port}")
        print()
        
        async with async_playwright() as p:
            browser = None
            
            # Пытаемся подключиться к существующему Chrome
            if connect_to_existing:
                try:
                    print(f"🔗 Подключаемся к запущенному Chrome на порту {debug_port}...")
                    browser = await p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
                    print("✅ Успешно подключились к запущенному Chrome!")
                except Exception as e:
                    print(f"❌ Не удалось подключиться: {e}")
                    print("💡 Убедитесь, что Chrome запущен с --remote-debugging-port=9222")
                    return False
            
            # Или запускаем новый Chrome
            elif use_installed_chrome:
                # Автопоиск Chrome если путь не указан
                if not chrome_path:
                    chrome_paths = [
                        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
                        '/usr/bin/google-chrome',  # Linux
                        '/usr/bin/google-chrome-stable',  # Linux
                        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
                        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'  # Windows 32-bit
                    ]
                    
                    for path in chrome_paths:
                        if os.path.exists(path):
                            chrome_path = path
                            break
                
                if chrome_path and os.path.exists(chrome_path):
                    print(f"🚀 Запускаем Chrome: {chrome_path}")
                    browser = await p.chromium.launch(
                        headless=False,
                        executable_path=chrome_path,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    print("✅ Chrome запущен успешно!")
                else:
                    print("❌ Chrome не найден")
                    return False
            else:
                print("🌐 Используем встроенный Chromium...")
                browser = await p.chromium.launch(headless=False)
            
            # Создаем страницу и проверяем IP
            if browser:
                print("\n🌍 Проверяем IP адрес...")
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # Переходим на сайт для проверки IP
                    await page.goto('https://httpbin.org/ip', timeout=10000)
                    await page.wait_for_load_state('networkidle')
                    
                    # Получаем IP
                    ip_text = await page.text_content('body')
                    print(f"📍 Ваш IP: {ip_text}")
                    
                    # Проверяем доступность Allegro
                    print("\n🔍 Проверяем доступность Allegro.pl...")
                    await page.goto('https://allegro.pl', timeout=15000)
                    await page.wait_for_load_state('domcontentloaded')
                    
                    title = await page.title()
                    print(f"✅ Allegro.pl доступен! Заголовок: {title}")
                    
                    # Проверяем, есть ли блокировка
                    page_content = await page.content()
                    if 'blocked' in page_content.lower() or 'access denied' in page_content.lower():
                        print("⚠️ Возможна блокировка доступа")
                    else:
                        print("✅ Доступ к Allegro.pl работает!")
                    
                except Exception as e:
                    print(f"❌ Ошибка при проверке: {e}")
                
                finally:
                    await browser.close()
                    
                return True
            
    except ImportError:
        print("❌ Playwright не установлен")
        print("💡 Установите: pip install playwright")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Главная функция"""
    print("🧪 Тест подключения Chrome с VPN")
    print("=" * 40)
    
    # Проверяем .env файл
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден")
        print("💡 Запустите: ./setup_chrome_vpn.sh")
        return
    
    # Запускаем тест
    try:
        result = asyncio.run(test_chrome_connection())
        if result:
            print("\n🎉 Тест прошел успешно!")
            print("💡 Теперь можете запускать приложение: ./run.sh")
        else:
            print("\n❌ Тест не прошел")
            print("💡 Проверьте настройки в .env файле")
    except KeyboardInterrupt:
        print("\n🛑 Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка теста: {e}")

if __name__ == "__main__":
    main()
