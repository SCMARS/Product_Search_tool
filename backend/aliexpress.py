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
        'mouse': ['wireless mouse', 'gaming mouse', 'computer mouse']
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
    
    # Расширенный словарь товаров для разных категорий
    product_templates = {
        'массажер': [
            {'name': 'Electric Massage Gun Deep Tissue Massager 30 Speed', 'price': '$29.99', 'category': 'Health & Beauty'},
            {'name': 'Shiatsu Back Neck Massager with Heat Function', 'price': '$45.50', 'category': 'Health & Beauty'},
            {'name': 'Foot Massager Machine with Heat and Air Compression', 'price': '$89.99', 'category': 'Health & Beauty'},
            {'name': 'Handheld Electric Massager for Body Muscle Relief', 'price': '$19.99', 'category': 'Health & Beauty'},
            {'name': 'Cervical Massage Pillow for Neck and Shoulder Pain', 'price': '$35.99', 'category': 'Health & Beauty'}
        ],
        'массажор': [  # Добавляем для опечатки
            {'name': 'Electric Massage Gun Deep Tissue Massager 30 Speed', 'price': '$29.99', 'category': 'Health & Beauty'},
            {'name': 'Professional Massage Gun for Athletes', 'price': '$69.99', 'category': 'Health & Beauty'},
            {'name': 'Portable Electric Massager USB Rechargeable', 'price': '$24.99', 'category': 'Health & Beauty'},
            {'name': 'Deep Tissue Massage Gun with 6 Heads', 'price': '$49.99', 'category': 'Health & Beauty'},
            {'name': 'Wireless Rechargeable Massage Gun Quiet Motor', 'price': '$39.99', 'category': 'Health & Beauty'}
        ],
        'iphone': [
            {'name': 'Phone Case for iPhone 15 Pro Max Clear', 'price': '$8.99', 'category': 'Phone Accessories'},
            {'name': 'Wireless Charger for iPhone 15W Fast Charging', 'price': '$12.99', 'category': 'Phone Accessories'},
            {'name': 'Screen Protector for iPhone Tempered Glass', 'price': '$5.99', 'category': 'Phone Accessories'},
            {'name': 'Phone Holder Car Mount for iPhone', 'price': '$15.99', 'category': 'Phone Accessories'},
            {'name': 'Lightning Cable USB-C for iPhone Fast Charging', 'price': '$7.99', 'category': 'Phone Accessories'}
        ],
        'macbook air': [
            {'name': 'MacBook Air Case Hard Shell Cover 13 inch', 'price': '$16.99', 'category': 'Computer Accessories'},
            {'name': 'USB-C Hub for MacBook Air 7-in-1 Adapter', 'price': '$29.99', 'category': 'Computer Accessories'},
            {'name': 'MacBook Air Stand Aluminum Laptop Holder', 'price': '$24.99', 'category': 'Computer Accessories'},
            {'name': 'Wireless Mouse for MacBook Air Bluetooth', 'price': '$19.99', 'category': 'Computer Accessories'},
            {'name': 'MacBook Air Charger USB-C 67W Power Adapter', 'price': '$35.99', 'category': 'Computer Accessories'}
        ],
        'macbook': [
            {'name': 'MacBook Pro Case Hard Shell Cover 13 inch', 'price': '$16.99', 'category': 'Computer Accessories'},
            {'name': 'USB-C Hub for MacBook Pro 7-in-1 Adapter', 'price': '$29.99', 'category': 'Computer Accessories'},
            {'name': 'MacBook Stand Aluminum Laptop Holder', 'price': '$24.99', 'category': 'Computer Accessories'},
            {'name': 'Wireless Mouse for MacBook Bluetooth', 'price': '$19.99', 'category': 'Computer Accessories'},
            {'name': 'MacBook Charger USB-C 67W Power Adapter', 'price': '$35.99', 'category': 'Computer Accessories'}
        ],
        'фотоаппарат': [
            {'name': 'Digital Camera 4K Video Recording 48MP', 'price': '$159.99', 'category': 'Electronics'},
            {'name': 'Professional DSLR Camera with Lens Kit', 'price': '$299.99', 'category': 'Electronics'},
            {'name': 'Instant Camera Polaroid Style Photo Printer', 'price': '$79.99', 'category': 'Electronics'},
            {'name': 'Action Camera Waterproof 4K Sports Cam', 'price': '$49.99', 'category': 'Electronics'},
            {'name': 'Vintage Film Camera 35mm Manual Focus', 'price': '$89.99', 'category': 'Electronics'}
        ],
        'наушники': [
            {'name': 'Wireless Bluetooth Headphones Noise Cancelling', 'price': '$39.99', 'category': 'Electronics'},
            {'name': 'Gaming Headset with Microphone RGB LED', 'price': '$29.99', 'category': 'Electronics'},
            {'name': 'True Wireless Earbuds Bluetooth 5.0', 'price': '$19.99', 'category': 'Electronics'},
            {'name': 'Over Ear Headphones Studio Quality Sound', 'price': '$49.99', 'category': 'Electronics'},
            {'name': 'Sports Earphones Waterproof Running', 'price': '$24.99', 'category': 'Electronics'}
        ]
    }
    
    # Улучшенная логика определения категории
    query_lower = query.lower()
    selected_products = []
    
    # Сначала ищем точные совпадения
    if query_lower in product_templates:
        selected_products = product_templates[query_lower]
        logger.info(f"🎯 Точное совпадение категории: '{query_lower}'")
    else:
        # Ищем частичные совпадения с подсчетом релевантности
        matches = []
        for category, products in product_templates.items():
            # Подсчитываем количество совпадающих слов
            query_words = set(query_lower.split())
            category_words = set(category.split())
            
            # Проверяем точное вхождение категории в запрос
            if category in query_lower:
                matches.append((len(category), category, products))
            # Или проверяем пересечение слов
            elif query_words.intersection(category_words):
                intersection_count = len(query_words.intersection(category_words))
                matches.append((intersection_count, category, products))
        
        # Сортируем по количеству совпадений (больше совпадений = выше приоритет)
        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            selected_products = matches[0][2]
            logger.info(f"🎯 Выбрана категория: '{matches[0][1]}' для запроса: '{query}' (совпадений: {matches[0][0]})")
        else:
            # Fallback поиск по отдельным словам
            for category, products in product_templates.items():
                if any(word in category for word in query_lower.split()):
                    selected_products = products
                    logger.info(f"🎯 Fallback категория: '{category}' для запроса: '{query}'")
                    break
    
    # Если не нашли специфичную категорию, используем общие товары
    if not selected_products:
        selected_products = [
            {'name': f'{query.title()} High Quality Product', 'price': '$24.99', 'category': 'General'},
            {'name': f'Premium {query.title()} with Fast Shipping', 'price': '$39.99', 'category': 'General'},
            {'name': f'{query.title()} Professional Grade', 'price': '$59.99', 'category': 'General'},
            {'name': f'Best {query.title()} 2024 New Arrival', 'price': '$19.99', 'category': 'General'},
            {'name': f'{query.title()} Wholesale Price Direct', 'price': '$14.99', 'category': 'General'}
        ]
    
    # Создаем товары
    for i, template in enumerate(selected_products[:limit]):
        results.append({
            "name": template['name'],
            "price": template['price'],
            "url": f"https://www.aliexpress.com/item/{1234567890 + i}.html",
            "image": f"https://ae01.alicdn.com/kf/H{hash(template['name']) % 100000:05d}.jpg",
            "description": f"Источник: AliExpress - {template['category']}",
            "relevance_score": 75
        })
    
    logger.info(f"🏁 Поиск AliExpress завершен. Найдено товаров: {len(results)}")
    return results

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
