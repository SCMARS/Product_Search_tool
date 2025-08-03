#!/usr/bin/env python3
"""
Простой тест нового парсера Allegro без прокси
"""

import asyncio
import logging
import os
from allegro_enhanced import AllegroEnhancedScraper

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_search():
    """Простой тест поиска без прокси"""
    
    # Создаем скрапер
    scraper = AllegroEnhancedScraper()
    
    # Очищаем список прокси для теста
    scraper.proxy_list = []
    
    test_query = "iphone 15"
    
    logger.info(f"🧪 Тестируем простой поиск: '{test_query}'")
    logger.info("🌐 Прокси отключены для теста")
    
    try:
        # Запускаем поиск
        results = await scraper.search_products(test_query, max_pages=1, max_retries=1)
        
        if results:
            logger.info(f"✅ Найдено {len(results)} товаров:")
            for i, product in enumerate(results[:3], 1):
                logger.info(f"\n{i}. {product['name']}")
                logger.info(f"   💰 {product['price']}")
                logger.info(f"   🏪 {product['seller']}")
                logger.info(f"   📊 Релевантность: {product['relevance_score']:.1f}")
                logger.info(f"   🔗 {product['url']}")
        else:
            logger.warning("❌ Товары не найдены")
            
            # Пробуем fallback
            logger.info("🔄 Пробуем fallback метод...")
            fallback_results = scraper._fallback_simple_search(test_query)
            
            if fallback_results:
                logger.info(f"✅ Fallback: найдено {len(fallback_results)} товаров:")
                for i, product in enumerate(fallback_results[:3], 1):
                    logger.info(f"\n{i}. {product['name']}")
                    logger.info(f"   💰 {product['price']}")
                    logger.info(f"   📊 Релевантность: {product['relevance_score']:.1f}")
            else:
                logger.warning("❌ Fallback тоже не дал результатов")
    
    except Exception as e:
        logger.error(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_search())
