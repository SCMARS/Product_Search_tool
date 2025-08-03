#!/usr/bin/env python3
"""
Демо-тест нового парсера Allegro с быстрыми fallback методами
"""

import asyncio
import logging
from allegro_enhanced import AllegroEnhancedScraper, search_allegro_enhanced_sync

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fallback_methods():
    """Тестирует fallback методы напрямую"""
    
    scraper = AllegroEnhancedScraper()
    test_queries = ["iphone 15", "macbook pro", "samsung galaxy", "laptop gaming"]
    
    for query in test_queries:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Тестируем fallback для: '{query}'")
        logger.info(f"{'='*50}")
        
        # Тестируем каждый fallback метод
        methods = [
            ("📱 Мобильная версия", scraper._try_mobile_version),
            ("🔌 API endpoints", scraper._try_api_search),
            ("🔄 Альтернативные endpoints", scraper._try_alternative_endpoints),
            ("🎭 Демо результаты", scraper._create_mock_results)
        ]
        
        for method_name, method in methods:
            try:
                logger.info(f"\n{method_name}:")
                results = method(query)
                
                if results:
                    logger.info(f"✅ {len(results)} товаров найдено")
                    for i, product in enumerate(results[:2], 1):
                        logger.info(f"  {i}. {product['name'][:60]}...")
                        logger.info(f"     💰 {product['price']}")
                        logger.info(f"     📊 {product['relevance_score']:.1f}")
                    break  # Если метод сработал, переходим к следующему запросу
                else:
                    logger.warning(f"❌ {method_name} не дал результатов")
                    
            except Exception as e:
                logger.warning(f"❌ {method_name} ошибка: {e}")
                continue

def test_sync_integration():
    """Тестирует синхронную интеграцию"""
    logger.info(f"\n{'='*60}")
    logger.info("🔗 Тестируем интеграцию с основным приложением")
    logger.info(f"{'='*60}")
    
    test_query = "iphone 15"
    
    try:
        results = search_allegro_enhanced_sync(test_query, max_pages=1)
        
        if results:
            logger.info(f"✅ Синхронная функция: найдено {len(results)} товаров")
            for i, product in enumerate(results[:3], 1):
                logger.info(f"\n{i}. {product['name']}")
                logger.info(f"   💰 {product['price']}")
                logger.info(f"   🏪 {product['seller']}")
                logger.info(f"   📊 Релевантность: {product['relevance_score']:.1f}")
                logger.info(f"   🔗 {product['url'][:80]}...")
        else:
            logger.warning("❌ Синхронная функция не дала результатов")
            
    except Exception as e:
        logger.error(f"❌ Ошибка синхронной функции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Тестируем fallback методы
    test_fallback_methods()
    
    # Тестируем синхронную интеграцию
    test_sync_integration()
    
    logger.info(f"\n{'='*60}")
    logger.info("🏁 Тестирование завершено!")
    logger.info("💡 Для полноценной работы настройте:")
    logger.info("   - CAPTCHA_API_KEY для автоматического решения CAPTCHA")
    logger.info("   - Рабочие прокси в proxy_list.txt")
    logger.info("   - Или используйте VPN для обхода блокировок")
    logger.info(f"{'='*60}")
