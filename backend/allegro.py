import asyncio
import logging
import os
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllegroScraper:
    def __init__(self):
        self.search_url = "https://allegro.pl"

    def calculate_relevance_score(self, title: str, query: str) -> int:
        """
        Функция расчета релевантности товара
        """
        if not title or not query:
            return 0

        title_lower = title.lower()
        query_lower = query.lower()
        query_words = query_lower.split()

        score = 0

        # 1. Проверка на точное совпадение всего запроса
        if query_lower in title_lower:
            score += 100

        # 2. Проверяем каждое слово из запроса
        for query_word in query_words:
            if len(query_word) >= 2:
                if query_word in title_lower:
                    score += len(query_word) * 10

        # 3. Бонусы за ключевые слова
        key_terms = {
            'macbook': 50, 'mac': 30, 'apple': 25, 'iphone': 40,
            'samsung': 25, 'xiaomi': 25, 'huawei': 20,
            'laptop': 20, 'notebook': 20, 'pro': 15, 'max': 15,
            'm4': 40, 'm3': 30, 'm2': 20, 'm1': 15,
            'air': 20, 'mini': 15, 'chip': 10
        }

        for term, bonus in key_terms.items():
            if term in title_lower:
                score += bonus

        # 4. Штрафы за нерелевантные слова
        irrelevant_terms = [
            'case', 'obudowa', 'cover', 'pokrowiec', 'kabel', 'cable',
            'ładowarka', 'charger', 'adapter', 'mouse', 'mysz', 'keyboard',
            'klawiatura', 'stand', 'podstawka', 'bag', 'torba',
            'folia', 'protector', 'szkło', 'glass', 'blickschutz', 'filter',
            'hülle', 'entworfen', 'kompatibel', 'supershieldz'
        ]

        for term in irrelevant_terms:
            if term in title_lower:
                score -= 40

        return max(0, score)

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск товаров на Allegro
        """
        products = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()

                # Переходим на страницу поиска
                search_url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"
                logger.info(f"🔍 Поиск: {search_url}")

                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)

                # Обрабатываем GDPR
                try:
                    consent_button = page.locator('[data-role="accept-consent"]')
                    if await consent_button.count() > 0:
                        await consent_button.click()
                        await asyncio.sleep(2)
                        logger.info("✅ GDPR consent принят")
                except:
                    pass

                # Ищем товары с разными селекторами
                selectors_to_try = [
                    'div[data-role="offer"]',
                    'article[data-analytics-view-label]',
                    '[data-testid="listing-item"]',
                    'div[data-testid="web-listing-item"]'
                ]

                found_products = False

                for selector in selectors_to_try:
                    try:
                        elements = page.locator(selector)
                        count = await elements.count()

                        if count > 0:
                            logger.info(f"✅ Найдено {count} товаров с селектором: {selector}")
                            found_products = True

                            # Парсим товары
                            for i in range(min(count, 30)):
                                try:
                                    element = elements.nth(i)

                                    # Извлекаем данные
                                    title_element = element.locator('a[href*="/oferta/"]').first
                                    title = await title_element.get_attribute('title') or await title_element.text_content()

                                    price_element = element.locator('span:has-text("zł")').first
                                    price = await price_element.text_content() if await price_element.count() > 0 else ""

                                    url = await title_element.get_attribute('href') if await title_element.count() > 0 else ""

                                    image_element = element.locator('img').first
                                    image = await image_element.get_attribute('src') if await image_element.count() > 0 else ""

                                    if title and price:
                                        title = title.strip()
                                        price = price.strip()

                                        # Считаем релевантность
                                        score = self.calculate_relevance_score(title, query)

                                        logger.info(f"📦 {i+1}. {title[:70]}... | {price} | Score: {score}")

                                        if score >= 30:  # Минимальный порог
                                            product = {
                                                'name': title,
                                                'price': price,
                                                'url': url if url.startswith('http') else f"https://allegro.pl{url}",
                                                'image': image,
                                                'description': f"Источник: Allegro, Релевантность: {score}",
                                                'relevance_score': score
                                            }
                                            products.append(product)
                                            logger.info(f"✅ Товар добавлен!")
                                        else:
                                            logger.info(f"❌ Товар пропущен (низкая релевантность)")

                                except Exception as e:
                                    logger.debug(f"Ошибка парсинга товара {i}: {e}")
                                    continue

                            break  # Выходим из цикла если нашли товары

                    except Exception as e:
                        logger.debug(f"Селектор {selector} не сработал: {e}")
                        continue

                if not found_products:
                    logger.error("❌ Товары не найдены ни с одним селектором")

                await browser.close()

        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")

        # Сортируем по релевантности
        products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        logger.info(f"🏁 Найдено {len(products)} релевантных товаров")
        return products

# Синхронная обертка
def search_allegro_improved(query: str, max_pages: int = 1, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Основная функция для поиска на Allegro
    """
    try:
        scraper = AllegroScraper()
        return asyncio.run(scraper.search_products(query))
    except Exception as e:
        logger.error(f"❌ Ошибка в search_allegro_improved: {e}")
        return []

# Функции для создания листингов (упрощенные)
def generate_product_description(product_name: str, price: str) -> str:
    name_lower = product_name.lower()

    if any(word in name_lower for word in ['macbook', 'laptop', 'notebook']):
        return f"{product_name}\n\n✅ Profesjonalny Laptop\n\nWydajny komputer przenośny idealny do pracy, nauki i rozrywki."
    elif any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi']):
        return f"{product_name}\n\n✅ Wysokiej Jakości Smartfon\n\nIdealny telefon komórkowy z najnowszymi funkcjami."
    else:
        return f"{product_name}\n\n✅ Wysokiej Jakości Produkt\n\nProfesjonalny produkt najwyższej jakości."

def generate_product_parameters(product_name: str) -> Dict[str, str]:
    return {
        'Stan': 'Nowy',
        'Faktura': 'Wystawiam fakturę VAT',
        'Marka': 'Oryginalna'
    }

def determine_category(product_name: str) -> str:
    name_lower = product_name.lower()
    if any(word in name_lower for word in ['macbook', 'laptop', 'notebook']):
        return 'Komputery'
    return 'Elektronika'

def generate_tags(product_name: str) -> List[str]:
    return ['nowy', 'oryginalny', 'gwarancja']

def generate_highlights(product_name: str) -> List[str]:
    return ['✅ Nowy produkt', '✅ Pełna gwarancja']

def generate_features(product_name: str) -> List[str]:
    return ['Oryginalny produkt', 'Pełna gwarancja']

def create_full_allegro_listing(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Создает шаблон объявления для Allegro"""
    product_name = product_data.get('name', '')
    price = product_data.get('price', '')

    return {
        'title': product_name,
        'price': price,
        'description': generate_product_description(product_name, price),
        'parameters': generate_product_parameters(product_name),
        'images': [product_data.get('image', '')],
        'category': determine_category(product_name),
        'condition': 'Nowy',
        'warranty': 'Gwarancja producenta',
        'shipping': 'Darmowa dostawa',
        'payment': 'Przelew online, Pobranie',
        'tags': generate_tags(product_name),
        'highlights': generate_highlights(product_name),
        'features': generate_features(product_name)
    }

# Тест
async def test_search():
    scraper = AllegroScraper()
    results = await scraper.search_products("macbook m4 pro")

    print(f"\n🎯 Найдено товаров: {len(results)}")
    for i, product in enumerate(results[:5]):
        print(f"{i+1}. {product['name'][:60]}...")
        print(f"   Цена: {product['price']}")
        print(f"   Релевантность: {product['relevance_score']}")
        print()

if __name__ == "__main__":
    asyncio.run(test_search())