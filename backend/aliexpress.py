
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
    try:
        api_results = search_aliexpress_api(query, limit)
        if api_results:
            logger.info(f"✅ RapidAPI поиск успешен: найдено {len(api_results)} товаров")
            return api_results
    except Exception as e:
        logger.warning(f"⚠️ RapidAPI поиск не удался: {e}")


    logger.info("🔄 Попытка HTML-скрапинга на AliExpress")
    return scrape_aliexpress(query, limit)


def scrape_aliexpress(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Скрапинг результатов поиска AliExpress с обновленными селекторами"""
    results: List[Dict[str, Any]] = []
    encoded = quote_plus(query)
    url = f"{ALIEXPRESS_BASE}?SearchText={encoded}"
    logger.info(f"🔍 Скрейпер: запрос {url}")

    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        logger.error(f"❌ Скрапинг не удался, статус: {resp.status_code}")
        return results

    soup = BeautifulSoup(resp.text, 'html.parser')


    card_selectors = [
        'div._3t7zg',  # старый селектор
        'div[data-widget-cid]',  # новый селектор
        'div.list-item',
        'div.product-item',
        'div[class*="item"]',
        'a[href*="/item/"]',  # ссылки на товары
        'div[class*="product"]'
    ]

    items = []
    for selector in card_selectors:
        items = soup.select(selector)
        if items:
            logger.info(f"✅ Найдено {len(items)} товаров с селектором: {selector}")
            break

    if not items:
        logger.warning("⚠️ Товары не найдены ни с одним селектором")
        return results

    for card in items[:limit]:
        try:
            # Пробуем разные способы извлечения данных
            name = ""
            url = ""
            price = ""
            image = ""

            # Извлекаем название и ссылку
            title_selectors = [
                'a._3t7zg._2f4Ho span._2tW1I',  # старый
                'a[href*="/item/"]',  # новый
                'h3 a',
                'a[title]',
                '.item-title a',
                'a span'
            ]

            for title_sel in title_selectors:
                title_el = card.select_one(title_sel)
                if title_el:
                    name = title_el.get_text(strip=True) or title_el.get('title', '')
                    # Получаем ссылку из того же элемента или родителя
                    link_el = title_el if title_el.name == 'a' else title_el.find_parent('a')
                    if link_el:
                        url = link_el.get('href', '')
                    break

            # Если не нашли через title селекторы, ищем любую ссылку на товар
            if not name or not url:
                link_el = card.select_one('a[href*="/item/"]')
                if link_el:
                    url = link_el.get('href', '')
                    name = link_el.get_text(strip=True) or link_el.get('title', '')

            # Извлекаем цену
            price_selectors = [
                'div._1w9jL span._12A8D',  # старый
                'span[class*="price"]',
                'div[class*="price"]',
                '.price',
                'span:contains("$")',
                'span:contains("€")',
                'span:contains("₽")'
            ]

            for price_sel in price_selectors:
                price_el = card.select_one(price_sel)
                if price_el:
                    price = price_el.get_text(strip=True)
                    if price and any(symbol in price for symbol in ['$', '€', '₽', 'US']):
                        break

            # Если цену не нашли, ищем любой текст с валютными символами
            if not price:
                all_text = card.get_text()
                import re
                price_match = re.search(r'[\$€₽]\s*\d+[.,]?\d*|\d+[.,]?\d*\s*[\$€₽]|US\s*\$\s*\d+[.,]?\d*', all_text)
                if price_match:
                    price = price_match.group().strip()

            # Извлекаем изображение
            img_selectors = [
                'img._2r_T-',  # старый
                'img[src*="alicdn"]',
                'img[data-src*="alicdn"]',
                'img[src]',
                'img[data-src]'
            ]

            for img_sel in img_selectors:
                img_el = card.select_one(img_sel)
                if img_el:
                    image = img_el.get('src') or img_el.get('data-src', '')
                    if image:
                        break

            # Проверяем что у нас есть минимальные данные
            if name and len(name) > 5:
                # Исправляем URL
                if url and not url.startswith('http'):
                    if url.startswith('//'):
                        url = f"https:{url}"
                    elif url.startswith('/'):
                        url = f"https://www.aliexpress.com{url}"

                results.append({
                    'name': name,
                    'price': price if price else "Цена не указана",
                    'url': url,
                    'image': image,
                    'description': 'Источник: AliExpress (scraped)',
                    'relevance_score': 70
                })
                logger.info(f"✅ Скрапинг товар: {name[:50]} - {price}")
        except Exception as ex:
            logger.debug(f"Ошибка обработки карточки: {ex}")
            continue

    logger.info(f"✅ Скрапинг завершен: найдено {len(results)} товаров")
    return results


def search_aliexpress_api(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Работа через RapidAPI AliExpress DataHub используя http.client"""
    api_key = os.environ.get("RAPIDAPI_KEY", "")
    if not api_key:
        logger.warning("⚠️ RAPIDAPI_KEY не найден, пропускаем API поиск")
        raise RuntimeError("RAPIDAPI_KEY not configured")

    logger.info(f"🔑 Используем RapidAPI ключ: {api_key[:10]}...")

    try:

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        conn = http.client.HTTPSConnection("aliexpress-datahub.p.rapidapi.com", context=context)

        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "aliexpress-datahub.p.rapidapi.com"
        }


        params = {
            "q": query,
            "page": "1"
        }

        # Создаем URL с параметрами для рабочего эндпоинта
        query_string = urlencode(params)
        endpoint = f"/item_search_2?{query_string}"

        logger.info(f"🔍 API запрос: {endpoint}")

        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()

        logger.info(f"📡 API ответ: {res.status}")

        if res.status != 200:
            conn.close()
            raise RuntimeError(f"API returned {res.status}")

        response_text = data.decode("utf-8")
        data_json = json.loads(response_text)

        conn.close()

        # Обрабатываем ответ с новой структурой
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
                            'description': 'Источник: AliExpress (API)',
                            'relevance_score': 85
                        })
                        logger.info(f"✅ API товар: {name[:50]} - ${price}")

                except Exception as e:
                    logger.debug(f"Ошибка обработки товара: {e}")
                    continue

        if items:
            logger.info(f"✅ AliExpress API успешен: найдено {len(items)} товаров")
            return items
        else:
            logger.warning("⚠️ AliExpress API не вернул товары")
            raise RuntimeError("API не вернул товары")

    except Exception as e:
        logger.error(f"❌ Ошибка AliExpress API: {e}")
        raise RuntimeError(f"AliExpress API error: {e}")



if __name__ == '__main__':
    results = search_aliexpress('iphone 15 pro max', 5)
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item['name']} - {item['price']} -> {item['url']}")
