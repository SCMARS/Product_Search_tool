#!/usr/bin/env python3
"""
Простой и надежный скрапер для AliExpress
"""

import requests
import json
import logging
from typing import List, Dict, Any
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_aliexpress(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Улучшенный поиск товаров на AliExpress с расширенными запросами"""
    results = []
    
    logger.info(f"🔍 Начинаем поиск на AliExpress: {query}")
    
    # Создаем варианты поисковых запросов для лучшего покрытия
    search_variants = [
        query,  # Оригинальный запрос
        query.replace('массажор', 'массажер'),  # Исправляем опечатки
        query.replace('массажер', 'massager'),  # Английский вариант
        query.replace('фотоаппарат', 'camera'),
        query.replace('телефон', 'phone'),
        query.replace('наушники', 'headphones'),
        query.replace('часы', 'watch'),
    ]
    
    # Расширенные синонимы и похожие термины для ВСЕХ товаров
    synonyms = {
        # Массажеры
        'массажер': ['massager', 'massage gun', 'massage device'],
        'массажор': ['massager', 'massage gun', 'massage device'],

        # Бренды телефонов
        'айфон': ['iphone', 'apple phone', 'smartphone'],
        'iphone': ['phone case', 'mobile phone', 'smartphone'],
        'самсунг': ['samsung', 'galaxy', 'samsung phone'],
        'samsung': ['galaxy', 'samsung phone', 'android phone'],
        'сяоми': ['xiaomi', 'redmi', 'mi phone'],
        'xiaomi': ['redmi', 'mi phone', 'android phone'],
        'хуавей': ['huawei', 'honor', 'huawei phone'],
        'huawei': ['honor', 'huawei phone', 'android phone'],

        # Ноутбуки
        'макбук': ['macbook', 'apple laptop', 'laptop'],
        'macbook': ['laptop case', 'laptop stand', 'laptop accessories'],
        'дел': ['dell', 'dell laptop', 'laptop'],
        'dell': ['dell laptop', 'laptop', 'computer'],
        'хп': ['hp', 'hp laptop', 'laptop'],
        'hp': ['hp laptop', 'laptop', 'computer'],
        'фотоаппарат': ['camera', 'digital camera', 'photo camera'],
        'camera': ['digital camera', 'photo camera', 'video camera'],
        'наушники': ['headphones', 'earphones', 'wireless headphones'],
        'headphones': ['earphones', 'wireless headphones', 'bluetooth headphones'],
        'часы': ['watch', 'smart watch', 'wrist watch'],
        'watch': ['smart watch', 'wrist watch', 'digital watch'],
        'laptop': ['notebook', 'computer', 'laptop accessories'],
        'телефон': ['phone', 'smartphone', 'mobile phone'],
        'phone': ['smartphone', 'mobile phone', 'phone case'],
        'планшет': ['tablet', 'ipad', 'tablet case'],
        'tablet': ['ipad', 'tablet case', 'tablet stand'],
        'клавиатура': ['keyboard', 'wireless keyboard', 'gaming keyboard'],
        'keyboard': ['wireless keyboard', 'gaming keyboard', 'mechanical keyboard'],
        'мышь': ['mouse', 'wireless mouse', 'gaming mouse'],
        'mouse': ['wireless mouse', 'gaming mouse', 'computer mouse'],
        
        # Инструменты
        'silicone caulking tools': ['silicone seam tool', 'caulking tool', 'silicone tool'],
        'caulking tools': ['caulking tool', 'seam tool', 'silicone tool'],
        'silicone tools': ['silicone tool', 'caulking tool', 'seam tool']
    }
    
    # Добавляем синонимы к вариантам поиска
    for word, syns in synonyms.items():
        if word in query.lower():
            search_variants.extend(syns[:1])  # Добавляем только первый синоним
    
    # Убираем дубликаты
    search_variants = list(set(search_variants))
    
    # Пробуем RapidAPI метод сначала
    try:
        api_results = search_aliexpress_api(query, limit)
        if api_results:
            logger.info(f"✅ RapidAPI поиск успешен: найдено {len(api_results)} товаров")
            return api_results
    except Exception as e:
        logger.error(f"❌ Ошибка RapidAPI поиска: {e}")

    # Если API не сработал, возвращаем пустой список
    logger.info(f"❌ API не сработал, возвращаем пустой список")
    return []

def search_aliexpress_api(query, limit=20):
    """Поиск товаров на AliExpress через RapidAPI DataHub"""
    results = []

    try:
        # RapidAPI endpoint для AliExpress DataHub
        url = "https://aliexpress-datahub.p.rapidapi.com/item_search"

        querystring = {
            "q": query,
            "page": "1",
            "sort": "SALE_PRICE_ASC",
            "locale": "en_US",
            "region": "US",
            "currency": "USD"
        }

        headers = {
            "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", "067bf13bb7msh29bf8d815f8744bp158f84jsnd4928e52ec6e"),
            "X-RapidAPI-Host": "aliexpress-datahub.p.rapidapi.com"
        }

        logger.info(f"🔍 AliExpress API поиск: {query}")
        
        response = requests.get(url, headers=headers, params=querystring, timeout=30)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API ответ получен, статус: {response.status_code}")
            
            # Проверяем структуру ответа
            products = []
            if 'result' in data:
                result = data['result']
                if isinstance(result, dict) and 'resultList' in result:
                    products = result['resultList']
                elif isinstance(result, list):
                    products = result
            
            logger.info(f"📦 Найдено товаров в API: {len(products)}")

            for product in products[:limit]:
                try:
                    # Парсим данные товара из AliExpress DataHub API
                    name = product.get("title", {}).get("displayTitle", "") or product.get("title", "")
                    
                    # Парсим цену
                    price_info = product.get("prices", {})
                    if price_info and "salePrice" in price_info:
                        sale_price = price_info["salePrice"]
                        if isinstance(sale_price, dict):
                            price = f"${sale_price.get('minPrice', 'N/A')}"
                        else:
                            price = f"${sale_price}"
                    else:
                        price = "Price not available"
                    
                    # URL товара
                    product_url = product.get("productDetailUrl", "")
                    if product_url and not product_url.startswith("http"):
                        product_url = f"https:{product_url}"
                    
                    # Изображение товара
                    image_info = product.get("image", {})
                    if isinstance(image_info, dict):
                        image_url = image_info.get("imgUrl", "")
                    else:
                        image_url = str(image_info) if image_info else ""
                    
                    if image_url and not image_url.startswith("http"):
                        image_url = f"https:{image_url}"
                    
                    # Проверяем, что у нас есть минимально необходимые данные
                    if name and price != "Price not available":
                        results.append({
                            "name": name.strip(),
                            "price": price,
                            "image": image_url,
                            "url": product_url,
                            "description": f"Источник: AliExpress",
                            "relevance_score": 80
                        })
                        logger.info(f"📦 Найден товар: {name[:50]}... - {price}")

                except Exception as e:
                    logger.debug(f"Ошибка обработки товара: {str(e)}")
                    continue
                    
            logger.info(f"✅ API поиск завершен. Найдено товаров: {len(results)}")
            
        else:
            logger.error(f"❌ API запрос не удался. Статус: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Исключение во время API поиска: {str(e)}")

    return results

if __name__ == "__main__":
    # Тест
    query = "массажор"
    results = search_aliexpress(query, 5)
    print(f"Найдено {len(results)} товаров для '{query}':")
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']} - {product['price']}")
