
import requests
import json
import logging
import http.client
import ssl
from typing import List, Dict, Any
from urllib.parse import quote_plus, urlencode
from bs4 import BeautifulSoup
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ALIEXPRESS_BASE = "https://www.aliexpress.com/wholesale"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/115.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}


def search_aliexpress(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Поиск товаров на AliExpress ТОЛЬКО через API
    """
    results = []
    
    try:
        # Используем только API поиск
        api_results = search_aliexpress_api(query, limit)
        if api_results:
            logger.info(f"✅ RapidAPI поиск успешен: найдено {len(api_results)} товаров")
            return api_results
        else:
            logger.warning("⚠️ API не вернул результаты")
            return results
    except Exception as e:
        logger.error(f"❌ Ошибка AliExpress API: {e}")
        return results


def search_aliexpress_api(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Работа через RapidAPI AliExpress DataHub"""
    # Используем предоставленный ключ
    api_key = "30fbd6eb3cmsh237fee1bd93a580p167775jsne5d2245df248"
    
    logger.info(f"🔑 Используем RapidAPI ключ: {api_key[:10]}...")

    try:
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "aliexpress-datahub.p.rapidapi.com"
        }

        # Используем requests вместо http.client для более простой работы
        url = "https://aliexpress-datahub.p.rapidapi.com/item_search_2"
        params = {
            "q": query,
            "page": "1"
        }

        logger.info(f"🔍 API запрос: {url} с параметрами {params}")

        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        logger.info(f"📡 API ответ: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"❌ API вернул ошибку {response.status_code}: {response.text}")
            return []

        data_json = response.json()
        items = []

        logger.info(f"📦 Получены данные: {type(data_json)}")

        if 'result' in data_json:
            result = data_json['result']

            # Проверяем статус
            status = result.get('status', {})
            if status.get('code') != 200:
                logger.warning(f"⚠️ API статус: {status.get('code')}, сообщение: {status.get('msg', {})}")

            result_list = result.get('resultList', [])
            logger.info(f"📋 Найдено товаров в ответе: {len(result_list)}")

            for prod_wrapper in result_list[:limit]:
                try:
                    # Товар находится в поле 'item'
                    prod = prod_wrapper.get('item', {})
                    if not prod:
                        continue

                    # Извлекаем название
                    name = prod.get('title', '')

                    # Извлекаем цену из sku.def
                    price = ""
                    sku = prod.get('sku', {})
                    if sku and 'def' in sku:
                        sku_def = sku['def']
                        price = sku_def.get('promotionPrice') or sku_def.get('price')

                    # Извлекаем URL
                    item_url = prod.get('itemUrl', '')
                    full_url = f"https:{item_url}" if item_url.startswith('//') else item_url
                    if not full_url.startswith('http'):
                        full_url = f"https://www.aliexpress.com{item_url}"

                    # Извлекаем изображение
                    image = prod.get('image', '')
                    if image and image.startswith('//'):
                        image = f"https:{image}"

                    if name and len(name) > 5:
                        items.append({
                            'name': name,
                            'price': f"${price}" if price else "Цена не указана",
                            'url': full_url,
                            'image': image,
                            'relevance_score': 85,
                            'source': 'AliExpress'
                        })
                        logger.info(f"✅ API товар: {name[:50]} - ${price}")

                except Exception as e:
                    logger.error(f"Ошибка обработки товара: {e}")
                    continue

        if items:
            logger.info(f"✅ AliExpress API успешен: найдено {len(items)} товаров")
            return items
        else:
            logger.warning("⚠️ AliExpress API не вернул товары")
            return []

    except Exception as e:
        logger.error(f"❌ Ошибка AliExpress API: {e}")
        return []



if __name__ == '__main__':
    results = search_aliexpress('iphone 15 pro max', 5)
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item['name']} - {item['price']} -> {item['url']}")
