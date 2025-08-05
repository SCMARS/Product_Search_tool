
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


# Удаляем функцию scrape_aliexpress - больше не нужна
# def scrape_aliexpress(query: str, limit: int = 20) -> List[Dict[str, Any]]:
#     """Скрапинг результатов поиска AliExpress с обновленными селекторами"""
#     results: List[Dict[str, Any]] = []
#     encoded = quote_plus(query)
#     url = f"{ALIEXPRESS_BASE}?SearchText={encoded}"
#     logger.info(f"🔍 Скрейпер: запрос {url}")

#     try:
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Cache-Control': 'no-cache'
#         }

#         resp = requests.get(url, headers=headers, timeout=20)
#         if resp.status_code != 200:
#             logger.error(f"❌ Скрапинг не удался, статус: {resp.status_code}")
#             return results

#         soup = BeautifulSoup(resp.text, 'html.parser')

#         # Обновленные селекторы для поиска товаров
#         card_selectors = [
#             'div[data-widget-cid]',  # новый селектор
#             'div._3t7zg',  # старый селектор
#             'div.list-item',
#             'div.product-item',
#             'div[class*="item"]',
#             'a[href*="/item/"]',  # ссылки на товары
#             'div[class*="product"]',
#             'div[class*="card"]',
#             'div[class*="list"]'
#         ]

#         items = []
#         for selector in card_selectors:
#             items = soup.select(selector)
#             if items:
#                 logger.info(f"✅ Найдено {len(items)} товаров с селектором: {selector}")
#                 break

#         if not items:
#             logger.warning("⚠️ Товары не найдены ни с одним селектором")
#             # Попробуем найти любые ссылки на товары
#             items = soup.find_all('a', href=lambda x: x and '/item/' in x)
#             if items:
#                 logger.info(f"✅ Найдено {len(items)} ссылок на товары")

#         for card in items[:limit]:
#             try:
#                 # Извлекаем данные товара
#                 name = ""
#                 url = ""
#                 price = ""
#                 image = ""

#                 # Название товара
#                 title_selectors = [
#                     'a[href*="/item/"] span',
#                     'a[href*="/item/"]',
#                     'h3 a',
#                     'a[title]',
#                     '.item-title a',
#                     'a span',
#                     'span[class*="title"]',
#                     'div[class*="title"]'
#                 ]

#                 for title_sel in title_selectors:
#                     title_el = card.select_one(title_sel)
#                     if title_el:
#                         name = title_el.get_text(strip=True) or title_el.get('title', '')
#                         if name and len(name) > 5:
#                             break

#                 # Если название не найдено, попробуем извлечь из атрибута title
#                 if not name:
#                     title_attr = card.get('title') or card.find('a', title=True)
#                     if title_attr:
#                         name = title_attr.get('title', '') if hasattr(title_attr, 'get') else str(title_attr)

#                 if not name:
#                     continue

#                 # Ссылка на товар
#                 link_selectors = [
#                     'a[href*="/item/"]',
#                     'a[href*="/product/"]',
#                     'a[title]'
#                 ]

#                 for link_sel in link_selectors:
#                     link_el = card.select_one(link_sel)
#                     if link_el:
#                         url = link_el.get('href', '')
#                         if url and ('/item/' in url or '/product/' in url):
#                             if not url.startswith('http'):
#                                 url = f"https://www.aliexpress.com{url}"
#                             break

#                 # Цена
#                 price_selectors = [
#                     'span[class*="price"]',
#                     'div[class*="price"]',
#                     '.price',
#                     'span[data-currency]',
#                     'div[data-currency]'
#                 ]

#                 for price_sel in price_selectors:
#                     price_el = card.select_one(price_sel)
#                     if price_el:
#                         price_text = price_el.get_text(strip=True)
#                         if price_text and any(char.isdigit() for char in price_text):
#                             price = price_text
#                             break

#                 # Изображение
#                 img_selectors = [
#                     'img[src*="ae01.alicdn.com"]',
#                     'img[data-src]',
#                     'img[src]',
#                     'img'
#                 ]

#                 for img_sel in img_selectors:
#                     img_el = card.select_one(img_sel)
#                     if img_el:
#                         image = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy-src')
#                         if image and ('ae01.alicdn.com' in image or 'alicdn.com' in image):
#                             break

#                 # Создаем результат
#                 if name and url:
#                     result = {
#                         'name': name,
#                         'price': price or "Цена не указана",
#                         'image': image,
#                         'url': url,
#                         'relevance_score': 100,  # Базовый score
#                         'source': 'AliExpress'
#                     }
#                     results.append(result)
#                     logger.info(f"✅ Добавлен товар AliExpress: {name[:50]}...")

#             except Exception as e:
#                 logger.error(f"Error processing AliExpress item: {e}")
#                 continue

#         logger.info(f"🎯 Найдено {len(results)} товаров на AliExpress")
#         return results

#     except Exception as e:
#         logger.error(f"Error scraping AliExpress: {e}")
#         return results


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
