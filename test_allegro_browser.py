#!/usr/bin/env python3
"""
Тестовый скрипт для запуска поиска Allegro в видимом браузере Chrome
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from allegro_enhanced import search_allegro_enhanced

async def test_allegro_with_visible_browser():
    """
    Тестируем поиск Allegro с видимым браузером Chrome
    """
    print("🧪 Запускаем тест поиска Allegro с видимым браузером...")
    print("📱 Браузер Chrome откроется в видимом режиме")
    print("👀 Вы сможете увидеть, что именно происходит на сайте Allegro")
    print("=" * 60)
    
    try:
        # Тестовый запрос
        query = "iphone 15 pro"
        print(f"🔍 Поисковый запрос: '{query}'")
        print("⏳ Запускаем поиск...")
        
        # Запускаем поиск с отладкой
        results = await search_allegro_enhanced(query, max_pages=1, debug_mode=True)
        
        print("=" * 60)
        print(f"✅ Поиск завершен! Найдено товаров: {len(results)}")
        
        if results:
            print("\n📦 Первые 3 результата:")
            for i, product in enumerate(results[:3]):
                print(f"\n{i+1}. {product['name'][:80]}...")
                print(f"   💰 Цена: {product['price']}")
                print(f"   🔗 URL: {product['url'][:60]}...")
                print(f"   ⭐ Релевантность: {product.get('relevance_score', 0):.1f}")
        else:
            print("❌ Товары не найдены")
            print("🔍 Проверьте браузер - возможно, есть блокировка или CAPTCHA")
            
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Тест завершен")

if __name__ == "__main__":
    print("🚀 Запуск теста поиска Allegro...")
    print("💡 Убедитесь, что у вас установлены все зависимости:")
    print("   pip install playwright beautifulsoup4 requests python-dotenv")
    print("   playwright install chromium")
    print()
    
    # Запускаем тест
    asyncio.run(test_allegro_with_visible_browser())
