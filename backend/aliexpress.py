import os
import http.client
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
from urllib.parse import quote_plus

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Новый ключ для Aliexpress DataHub API
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") or "067bf13bb7msh29bf8d815f8744bp158f84jsnd4928e52ec6e"
API_HOST = "aliexpress-datahub.p.rapidapi.com"

def search_aliexpress(query: str, page: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Поиск товаров на AliExpress через Aliexpress DataHub API
    """
    if not query or not query.strip():
        logger.warning("Пустой поисковый запрос")
        return []

    try:
        # Создаем соединение
        conn = http.client.HTTPSConnection(API_HOST)

        # Формируем заголовки
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': API_HOST
        }

        # URL encode запрос для избежания проблем с пробелами
        encoded_query = quote_plus(query.strip())

        # Формируем URL с параметрами
        url = f"/item_search_2?q={encoded_query}&page={page}&sort=default"

        # Выполняем запрос
        conn.request("GET", url, headers=headers)

        # Получаем ответ
        res = conn.getresponse()
        data = res.read()

        logger.info(f"AliExpress DataHub API response status: {res.status}")

        if res.status == 200:
            # Парсим JSON ответ
            response_data = json.loads(data.decode("utf-8"))

            # Извлекаем товары из ответа (структура: result.resultList)
            products = []
            if isinstance(response_data, dict) and 'result' in response_data:
                result = response_data['result']
                if isinstance(result, dict) and 'resultList' in result:
                    products = result['resultList']
                elif isinstance(result, dict) and 'data' in result:
                    products = result['data']
                elif isinstance(result, list):
                    products = result
            elif isinstance(response_data, list):
                products = response_data

            # Преобразуем в нужный формат
            formatted_products = []
            if isinstance(products, list):
                for product in products[:limit]:
                    if isinstance(product, dict) and 'item' in product:
                        item = product['item']
                        formatted_product = {
                            'name': item.get('title', 'Без названия'),
                            'price': item.get('sku', {}).get('def', {}).get('promotionPrice', item.get('sku', {}).get('def', {}).get('price', 'Цена не указана')),
                            'image': f"https:{item.get('image', '')}" if item.get('image') and item.get('image').startswith('//') else item.get('image', ''),
                            'url': f"https:{item.get('itemUrl', '')}" if item.get('itemUrl') and item.get('itemUrl').startswith('//') else item.get('itemUrl', ''),
                            'description': f"Rating: {item.get('averageStarRate', 'N/A')}/5, Reviews: {item.get('sales', '0')}, Source: AliExpress"
                        }
                        formatted_products.append(formatted_product)
                    elif isinstance(product, dict):
                        # Fallback для других форматов
                        formatted_product = {
                            'name': product.get('title', product.get('name', 'Без названия')),
                            'price': product.get('price', product.get('salePrice', 'Цена не указана')),
                            'image': product.get('image', product.get('img', '')),
                            'url': product.get('url', product.get('link', '')),
                            'description': f"Source: AliExpress - {product.get('title', product.get('name', 'Product'))}"
                        }
                        formatted_products.append(formatted_product)

            logger.info(f"Найдено товаров: {len(formatted_products)}")
            return formatted_products
        else:
            logger.error(f"HTTP {res.status}: {data.decode('utf-8')}")
            return []

    except Exception as e:
        logger.error(f"Ошибка при поиске на AliExpress: {str(e)}")
        return []

def test_aliexpress_api():
    """
    Тестовая функция для проверки работы API
    """
    print("Тестируем Aliexpress DataHub API...")
    result = search_aliexpress("phone", 1, 5)
    print(f"Результат: {len(result)} товаров найдено")
    if result:
        print("Первый товар:")
        print(json.dumps(result[0], ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    test_aliexpress_api()