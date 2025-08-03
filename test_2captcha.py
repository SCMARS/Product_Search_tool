#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы 2Captcha API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_2captcha_api():
    """Тестирует 2Captcha API"""
    
    print("🧪 Тестирование 2Captcha API")
    print("=" * 40)
    
    # Получаем API ключ
    api_key = os.getenv('CAPTCHA_API_KEY')
    
    if not api_key:
        print("❌ CAPTCHA_API_KEY не найден в .env файле")
        print("💡 Добавьте ваш API ключ от 2captcha.com в файл .env:")
        print("   CAPTCHA_API_KEY=your_api_key_here")
        return False
    
    print(f"🔑 API ключ найден: {api_key[:10]}...{api_key[-4:]}")
    
    # Проверяем баланс
    print("\n💰 Проверяем баланс аккаунта...")
    
    try:
        balance_url = "http://2captcha.com/res.php"
        balance_params = {
            'key': api_key,
            'action': 'getbalance'
        }
        
        response = requests.get(balance_url, params=balance_params, timeout=10)
        
        if response.status_code == 200:
            balance_text = response.text.strip()
            
            if balance_text.startswith('ERROR_'):
                print(f"❌ Ошибка API: {balance_text}")
                
                if balance_text == 'ERROR_WRONG_USER_KEY':
                    print("💡 Неверный API ключ. Проверьте ключ на 2captcha.com")
                elif balance_text == 'ERROR_KEY_DOES_NOT_EXIST':
                    print("💡 API ключ не существует")
                else:
                    print("💡 Проверьте настройки аккаунта на 2captcha.com")
                
                return False
            else:
                try:
                    balance = float(balance_text)
                    print(f"✅ Баланс аккаунта: ${balance:.4f}")
                    
                    if balance < 0.001:
                        print("⚠️ Низкий баланс! Пополните аккаунт на 2captcha.com")
                        print("💡 Минимальная стоимость решения CAPTCHA: $0.001-0.003")
                        return False
                    else:
                        print("✅ Баланс достаточный для решения CAPTCHA")
                        
                except ValueError:
                    print(f"❌ Неожиданный ответ API: {balance_text}")
                    return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    
    # Тестируем библиотеку 2captcha-python
    print("\n📚 Проверяем библиотеку 2captcha-python...")
    
    try:
        from twocaptcha import TwoCaptcha
        solver = TwoCaptcha(api_key)
        print("✅ Библиотека 2captcha-python импортирована успешно")
        
        # Проверяем баланс через библиотеку
        try:
            balance = solver.balance()
            print(f"✅ Баланс через библиотеку: ${balance}")
        except Exception as e:
            print(f"⚠️ Ошибка получения баланса через библиотеку: {e}")
            
    except ImportError:
        print("❌ Библиотека 2captcha-python не установлена")
        print("💡 Установите: pip install 2captcha-python")
        return False
    except Exception as e:
        print(f"❌ Ошибка инициализации 2captcha: {e}")
        return False
    
    print("\n🎉 Тест 2Captcha API прошел успешно!")
    print("💡 API готов к использованию для решения CAPTCHA")
    
    return True

def check_captcha_in_env():
    """Проверяет настройки CAPTCHA в .env файле"""
    
    print("\n🔍 Проверяем настройки в .env файле...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден")
        print("💡 Создайте файл: cp .env.example .env")
        return False
    
    # Читаем .env файл
    with open('.env', 'r') as f:
        env_content = f.read()
    
    if 'CAPTCHA_API_KEY=' in env_content:
        print("✅ CAPTCHA_API_KEY найден в .env")
        
        # Проверяем, не пустой ли ключ
        api_key = os.getenv('CAPTCHA_API_KEY')
        if api_key and api_key != 'your_2captcha_api_key_here':
            print("✅ API ключ настроен")
            return True
        else:
            print("⚠️ API ключ не настроен или использует значение по умолчанию")
            print("💡 Замените 'your_2captcha_api_key_here' на ваш реальный ключ")
            return False
    else:
        print("❌ CAPTCHA_API_KEY не найден в .env")
        print("💡 Добавьте строку: CAPTCHA_API_KEY=your_api_key_here")
        return False

def main():
    """Главная функция"""
    print("🤖 Диагностика 2Captcha для Product Search Tool")
    print("=" * 50)
    
    # Проверяем .env файл
    if not check_captcha_in_env():
        print("\n❌ Проблемы с настройкой .env файла")
        return
    
    # Тестируем API
    if test_2captcha_api():
        print("\n🎉 Все проверки прошли успешно!")
        print("💡 2Captcha готов к работе")
        print("\n📋 Следующие шаги:")
        print("1. Запустите приложение: ./run.sh")
        print("2. Попробуйте поиск на Allegro")
        print("3. При появлении CAPTCHA она будет решена автоматически")
    else:
        print("\n❌ Есть проблемы с настройкой 2Captcha")
        print("💡 Исправьте ошибки и запустите тест снова")

if __name__ == "__main__":
    main()
