import asyncio
import logging
import os
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем новый скрапер
try:
    from allegro_scraper import AllegroParser
    search_allegro_advanced = None  # Не используем, так как у нас есть AllegroParser
    logger.info("✅ AllegroParser успешно импортирован")
except ImportError as e:
    logger.warning(f"⚠️ Не удалось импортировать AllegroParser: {e}")
    search_allegro_advanced = None

class AllegroScraper:
    def __init__(self):
        self.search_url = "https://allegro.pl"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def calculate_relevance_score(self, title: str, query: str) -> float:
        """
        Функция расчета релевантности товара
        """
        if not title or not query:
            return 0

        # Универсальная поддержка кириллицы и транслитерации для ВСЕХ товаров
        transliteration_map = {
            # Массажеры
            'массажор': ['masażer', 'massage', 'massager', 'masaż'],
            'массажер': ['masażer', 'massage', 'massager', 'masaż'],
            # Техника Apple
            'макбук': ['macbook'],
            'айфон': ['iphone'],
            'айпад': ['ipad'],
            'про': ['pro'],
            'эпл': ['apple'],
            'воч': ['watch'],
            'эпл воч': ['apple watch'],

            # Другие бренды телефонов
            'самсунг': ['samsung'],
            'сяоми': ['xiaomi'],
            'ксяоми': ['xiaomi'],
            'хуавей': ['huawei'],
            'хонор': ['honor'],
            'опо': ['oppo'],
            'виво': ['vivo'],
            'реалми': ['realme'],
            'ван плас': ['oneplus'],
            'гугл': ['google'],
            'пиксель': ['pixel'],
            'нокиа': ['nokia'],
            'моторола': ['motorola'],

            # Бренды ноутбуков
            'дел': ['dell'],
            'хп': ['hp'],
            'леново': ['lenovo'],
            'асус': ['asus'],
            'эйсер': ['acer'],
            'мси': ['msi'],
            'сони': ['sony'],
            # Другие популярные товары
            'телефон': ['phone', 'telefon', 'smartphone'],
            'наушники': ['headphones', 'słuchawki', 'earphones'],
            'часы': ['watch', 'zegarek', 'smartwatch'],
            'фотоаппарат': ['camera', 'aparat', 'kamera'],
            'ноутбук': ['laptop', 'notebook'],
            'планшет': ['tablet'],
            'клавиатура': ['keyboard', 'klawiatura'],
            'мышь': ['mouse', 'mysz'],
            # Аксессуары
            'чехол': ['case', 'etui', 'cover', 'obudowa'],
            'зарядка': ['charger', 'ładowarka'],
            'кабель': ['cable', 'kabel'],
            'подставка': ['stand', 'podstawka'],
            'сумка': ['bag', 'torba'],
            'защита': ['protector', 'protection']
        }

        query_lower = query.lower()
        title_lower = title.lower()

        # Проверяем транслитерацию - НЕ возвращаем сразу, а добавляем к общему score
        transliteration_bonus = 0
        for ru_word, en_variants in transliteration_map.items():
            if ru_word in query_lower:
                for variant in en_variants:
                    if variant in title_lower:
                        transliteration_bonus = 80.0  # Высокий score для транслитерации
                        break

        query_words = query_lower.split()

        score = transliteration_bonus  # Начинаем с бонуса за транслитерацию

        # 1. Проверка на точное совпадение всего запроса
        if query_lower in title_lower:
            score += 100

        # 2. Проверяем каждое слово из запроса
        for query_word in query_words:
            if len(query_word) >= 2:
                if query_word in title_lower:
                    score += len(query_word) * 10

        # 3. Универсальные бонусы за ключевые слова для ВСЕХ категорий
        key_terms = {
            # Apple техника - увеличиваем бонусы для iPhone
            'macbook': 50, 'mac': 30, 'apple': 30, 'iphone': 60, 'ipad': 35,
            'm4': 40, 'm3': 30, 'm2': 20, 'm1': 15, 'air': 20, 'mini': 15,
            'pro': 25, 'max': 25, 'chip': 10, '15': 30, '16': 30, '14': 25,

            # Бренды телефонов
            'samsung': 30, 'xiaomi': 30, 'huawei': 25, 'honor': 25,
            'oppo': 25, 'vivo': 25, 'realme': 25, 'oneplus': 25,
            'google': 25, 'pixel': 30, 'nokia': 20, 'motorola': 20,

            # Бренды ноутбуков
            'dell': 20, 'hp': 20, 'lenovo': 20, 'asus': 20,
            'acer': 15, 'msi': 20, 'sony': 20, 'lg': 15,

            # Другие бренды
            'microsoft': 20, 'surface': 25, 'nintendo': 25, 'playstation': 25,

            # Категории товаров
            'laptop': 20, 'notebook': 20, 'phone': 30, 'telefon': 30,
            'smartphone': 35, 'tablet': 25, 'watch': 25, 'zegarek': 25,
            'headphones': 30, 'słuchawki': 30, 'camera': 25, 'aparat': 25,

            # Массажеры
            'masażer': 60, 'massage': 50, 'masaż': 40, 'massager': 50,
            'elektryczny': 20, 'wibrujący': 20, 'antycellulitowy': 25,
            'shiatsu': 30, 'poduszka': 15, 'pistolet': 25,

            # Характеристики
            'wireless': 15, 'bezprzewodowy': 15, 'bluetooth': 15,
            'usb': 10, 'type-c': 10, 'lightning': 10,
            'gaming': 15, 'gamingowy': 15, 'professional': 15
        }

        for term, bonus in key_terms.items():
            if term in title_lower:
                score += bonus

        # 4. Универсальная система штрафов для ВСЕХ товаров

        # Проверяем, есть ли основные ключевые слова из запроса
        main_keywords_found = 0
        for query_word in query_words:
            if len(query_word) >= 2 and query_word in title_lower:
                main_keywords_found += 1

        # Контекстная система штрафов - учитываем, что именно ищет пользователь
        if main_keywords_found > 0:  # Если есть хотя бы одно совпадение

            # Определяем, что ищет пользователь
            user_wants_accessory = any(term in query_lower for term in [
                'чехол', 'case', 'etui', 'cover', 'obudowa', 'pokrowiec', 'hülle',
                'защита', 'protector', 'folia', 'szkło', 'glass',
                'кабель', 'cable', 'kabel', 'зарядка', 'charger', 'ładowarka',
                'подставка', 'stand', 'podstawka', 'сумка', 'bag', 'torba'
            ])

            # Штрафы за аксессуары - ТОЛЬКО если пользователь НЕ ищет аксессуары
            if not user_wants_accessory:
                accessory_terms = [
                    'etui', 'case', 'obudowa', 'cover', 'pokrowiec', 'hülle',
                    'folia', 'protector', 'szkło', 'glass', 'displayschutzfolie',
                    'schutzhülle', 'screen', 'protector'
                ]

                for term in accessory_terms:
                    if term in title_lower:
                        score -= 20  # Уменьшаем штраф за аксессуары с 40 до 20

                # Штрафы за другие аксессуары
                irrelevant_terms = [
                    'kabel', 'cable', 'ładowarka', 'charger', 'adapter',
                    'stand', 'podstawka', 'uchwyt', 'holder', 'mount',
                    'torba', 'bag', 'plecak', 'backpack', 'tasche'
                ]

                for term in irrelevant_terms:
                    if term in title_lower:
                        score -= 30  # Уменьшаем штраф за нерелевантные товары с 60 до 30
            else:
                # Если пользователь ищет аксессуары, даем бонус за соответствующие термины
                accessory_bonus_terms = {
                    'etui': 30, 'case': 30, 'cover': 25, 'obudowa': 25,
                    'pokrowiec': 25, 'protector': 20, 'szkło': 20,
                    'kabel': 30, 'cable': 30, 'charger': 30, 'ładowarka': 30,
                    'stand': 25, 'podstawka': 25, 'bag': 25, 'torba': 25
                }

                for term, bonus in accessory_bonus_terms.items():
                    if term in title_lower:
                        score += bonus  # Бонус за аксессуары, если их ищем

            # Дополнительная проверка: если в названии есть предлоги, указывающие на аксессуар
            if any(word in title_lower for word in ['do', 'na', 'dla', 'for', 'für', 'to']):
                # Проверяем, не аксессуар ли это к другому устройству
                other_devices = ['telefon', 'phone', 'laptop', 'komputer', 'computer', 'tablet', 'ipad']
                if any(device in title_lower for device in other_devices):
                    # Но только если это не тот же тип устройства, что мы ищем
                    query_devices = set(query_lower.split()) & set(other_devices)
                    title_devices = set(title_lower.split()) & set(other_devices)
                    if not query_devices.intersection(title_devices):
                        score -= 80  # Штраф за аксессуары к другим устройствам

        else:
            # Если основных ключевых слов мало, применяем жесткие штрафы
            score -= 20  # Базовый штраф за низкое совпадение

        return max(0, score)

    def search_products_simple(self, query: str) -> List[Dict[str, Any]]:
        """
        Простой поиск через HTTP запросы
        """
        products = []

        try:
            # Формируем URL для поиска
            search_url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"
            logger.info(f"🔍 HTTP поиск: {search_url}")

            # Делаем запрос
            session = requests.Session()
            session.headers.update(self.headers)

            response = session.get(search_url, timeout=30)
            response.raise_for_status()

            # Парсим HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем товары по различным селекторам
            product_selectors = [
                'article[data-role="offer"]',
                'div[data-role="offer"]',
                'article[data-analytics-view-label]',
                '[data-testid="listing-item"]',
                'article',
                'div[class*="listing"]'
            ]

            found_products = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"✅ Найдено {len(elements)} элементов с селектором: {selector}")
                    found_products = elements
                    break

            if not found_products:
                logger.warning("⚠️ Товары не найдены ни с одним селектором")
                return products

            # Парсим найденные товары
            for i, element in enumerate(found_products[:20]):  # Ограничиваем до 20
                try:
                    # Ищем заголовок
                    title = ""
                    title_selectors = ['a[href*="/oferta/"]', 'h3 a', 'h2 a', 'a[title]']
                    for title_sel in title_selectors:
                        title_elem = element.select_one(title_sel)
                        if title_elem:
                            title = title_elem.get('title') or title_elem.get_text(strip=True)
                            if title:
                                break

                    # Ищем цену
                    price = ""
                    # BeautifulSoup не поддерживает :contains, поэтому ищем по-другому
                    price_elements = element.find_all(['span', 'div'], class_=re.compile(r'price', re.I))
                    for price_elem in price_elements:
                        price_text = price_elem.get_text(strip=True)
                        if 'zł' in price_text:
                            price = price_text
                            break

                    # Если не нашли по классу, ищем любой элемент с "zł"
                    if not price:
                        all_elements = element.find_all(text=re.compile(r'zł'))
                        for elem in all_elements:
                            parent = elem.parent
                            if parent:
                                price_text = parent.get_text(strip=True)
                                if 'zł' in price_text:
                                    price = price_text
                                    break

                    # Ищем ссылку
                    url = ""
                    link_elem = element.select_one('a[href*="/oferta/"]')
                    if link_elem:
                        url = link_elem.get('href')
                        if url and not url.startswith('http'):
                            url = f"https://allegro.pl{url}"

                    # Ищем изображение
                    image = ""
                    img_elem = element.select_one('img')
                    if img_elem:
                        image = img_elem.get('src') or img_elem.get('data-src', '')

                    if title and price:
                        # Считаем релевантность
                        score = self.calculate_relevance_score(title, query)

                        if score >= 25:  # Снижаем порог с 45 до 25 для большего охвата
                            product = {
                                'name': title,
                                'price': price,
                                'url': url,
                                'image': image,
                                'description': f"Источник: Allegro, Релевантность: {score}",
                                'relevance_score': score
                            }
                            products.append(product)
                            logger.info(f"Found matching product: {title[:50]}... (Score: {score})")
                        else:
                            logger.info(f"Skipping non-matching product: {title[:50]}... (Score: {score})")

                except Exception as e:
                    logger.debug(f"Ошибка парсинга товара {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Ошибка HTTP поиска: {e}")

        # Сортируем по релевантности
        products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        logger.info(f"🏁 HTTP поиск: найдено {len(products)} товаров")

        return products

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск товаров на Allegro
        """
        products = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,  # Включаем headless обратно
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',
                        '--disable-javascript'
                    ]
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='pl-PL',
                    timezone_id='Europe/Warsaw'
                )
                
                # Добавляем JavaScript для обхода детекции ботов
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                """)
                
                page = await context.new_page()

                # Переходим на страницу поиска
                search_url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"
                logger.info(f"🔍 Поиск: {search_url}")

                await page.goto(search_url, timeout=60000)  # Увеличиваем до 60 секунд
                await page.wait_for_load_state("domcontentloaded")

                # Обрабатываем GDPR более агрессивно
                gdpr_selectors = [
                    '[data-role="accept-consent"]',
                    'button[data-testid="consent-accept"]',
                    'button:has-text("Akceptuję")',
                    'button:has-text("Accept")',
                    'button:has-text("Zgadzam się")'
                ]

                for gdpr_selector in gdpr_selectors:
                    try:
                        consent_button = page.locator(gdpr_selector)
                        if await consent_button.count() > 0:
                            await consent_button.click()
                            await asyncio.sleep(3)
                            logger.info(f"✅ GDPR consent принят с селектором: {gdpr_selector}")
                            break
                    except:
                        continue

                await page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(5)  # Увеличиваем ожидание

                # Добавляем более детальную диагностику
                try:
                    # Сначала проверяем, загрузилась ли страница
                    page_title = await page.title()
                    logger.info(f"📄 Заголовок страницы: {page_title}")
                    
                    # Проверяем наличие результатов поиска
                    search_results = page.locator('div[data-testid="listing-container"]')
                    if await search_results.count() == 0:
                        logger.warning("⚠️ Контейнер результатов не найден")
                        
                    # Проверяем общее количество элементов на странице
                    all_elements = page.locator('*')
                    total_count = await all_elements.count()
                    logger.info(f"📊 Всего элементов на странице: {total_count}")
                    
                    # Пробуем найти любые товары
                    generic_selectors = ['article', 'div[data-role]', '[data-testid]']
                    for selector in generic_selectors:
                        count = await page.locator(selector).count()
                        logger.info(f"🔍 Элементов с селектором '{selector}': {count}")
                        
                except Exception as e:
                    logger.error(f"Ошибка диагностики: {e}")

                # Обновляем селекторы для поиска товаров - добавляем более общие селекторы
                selectors_to_try = [
                    'article[data-role="offer"]',
                    'div[data-role="offer"]',
                    'article[data-analytics-view-label]',
                    '[data-testid="listing-item"]',
                    'div[data-testid="web-listing-item"]',
                    'article[data-testid="listing-item"]',
                    'div[class*="listing-item"]',
                    'article[class*="offer"]',
                    'div[class*="offer-item"]',
                    'section[data-testid="listing-item"]',
                    # Добавляем более общие селекторы
                    'article',
                    'div[data-testid]',
                    '[data-testid*="item"]',
                    '[data-testid*="offer"]',
                    '[data-testid*="product"]',
                    'div[class*="item"]',
                    'section[class*="item"]'
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

                                    # Извлекаем данные - используем более гибкие селекторы
                                    title = ""
                                    url = ""

                                    # Пробуем разные способы получить заголовок и ссылку
                                    title_selectors = [
                                        'a[href*="/oferta/"]',
                                        'a[data-testid*="title"]',
                                        'a[data-testid*="name"]',
                                        'h3 a',
                                        'h2 a',
                                        'a[title]',
                                        'a'
                                    ]

                                    for title_selector in title_selectors:
                                        title_element = element.locator(title_selector).first
                                        if await title_element.count() > 0:
                                            title = await title_element.get_attribute('title') or await title_element.text_content()
                                            url = await title_element.get_attribute('href')
                                            if title and title.strip():
                                                break

                                    # Извлекаем цену
                                    price = ""
                                    price_selectors = [
                                        'span:has-text("zł")',
                                        '[data-testid*="price"]',
                                        'span[class*="price"]',
                                        'div[class*="price"]',
                                        'span:has-text("PLN")',
                                        'span:has-text(",")',
                                        '[data-testid="price-container"]',
                                        '[data-testid="price"]',
                                        'span[data-role="price"]'
                                    ]

                                    for price_selector in price_selectors:
                                        price_element = element.locator(price_selector).first
                                        if await price_element.count() > 0:
                                            price = await price_element.text_content()
                                            if price and price.strip() and ('zł' in price or ',' in price):
                                                break

                                    # Если цена не найдена, попробуем найти любой текст с числом и zł
                                    if not price:
                                        all_text = await element.text_content()
                                        import re
                                        price_match = re.search(r'\d+[,.]?\d*\s*zł', all_text)
                                        if price_match:
                                            price = price_match.group()

                                    # Извлекаем изображение
                                    image_element = element.locator('img').first
                                    image = await image_element.get_attribute('src') if await image_element.count() > 0 else ""

                                    if title and price:
                                        title = title.strip()
                                        price = price.strip()

                                        # Считаем релевантность
                                        score = self.calculate_relevance_score(title, query)

                                        logger.info(f"📦 {i+1}. {title[:70]}... | {price} | Score: {score}")

                                        if score >= 25:  # Снижаем порог с 45 до 25 для большего охвата
                                            # Исправляем URL
                                            if url and not url.startswith('http'):
                                                if url.startswith('/'):
                                                    url = f"https://allegro.pl{url}"
                                                else:
                                                    url = f"https://allegro.pl/{url}"
                                            elif not url:
                                                # Если URL не найден, создаем поисковую ссылку
                                                url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"

                                            product = {
                                                'name': title,
                                                'price': price if price else "Цена не указана",
                                                'url': url,
                                                'image': image,
                                                'description': f"Источник: Allegro, Релевантность: {score}",
                                                'relevance_score': score
                                            }
                                            products.append(product)
                                            logger.info(f"Found matching product: {title[:50]}... (Score: {score})")
                                        else:
                                            logger.info(f"Skipping non-matching product: {title[:50]}... (Score: {score} < 25)")

                                except Exception as e:
                                    logger.debug(f"Ошибка парсинга товара {i}: {e}")
                                    continue

                            break  # Выходим из цикла если нашли товары

                    except Exception as e:
                        logger.debug(f"Селектор {selector} не сработал: {e}")
                        continue

                if not found_products:
                    logger.error("❌ Товары не найдены ни с одним селектором")

                    # Дополнительная диагностика - попробуем найти любые ссылки на товары
                    try:
                        all_links = page.locator('a[href*="oferta"]')
                        links_count = await all_links.count()
                        logger.info(f"🔗 Найдено ссылок на товары: {links_count}")

                        if links_count > 0:
                            # Попробуем извлечь данные из первых нескольких ссылок
                            for i in range(min(links_count, 5)):
                                try:
                                    link = all_links.nth(i)
                                    title = await link.get_attribute('title') or await link.text_content()
                                    url = await link.get_attribute('href')

                                    if title and title.strip():
                                        score = self.calculate_relevance_score(title.strip(), query)
                                        logger.info(f"🔗 Найдена ссылка: {title[:50]}... (Score: {score})")

                                        if score >= 45:
                                            # Попробуем найти цену рядом с этой ссылкой
                                            parent = link.locator('xpath=..')
                                            price_element = parent.locator('span:has-text("zł")').first
                                            price = await price_element.text_content() if await price_element.count() > 0 else "Цена не указана"

                                            # Исправляем URL
                                            if url and not url.startswith('http'):
                                                if url.startswith('/'):
                                                    url = f"https://allegro.pl{url}"
                                                else:
                                                    url = f"https://allegro.pl/{url}"
                                            elif not url:
                                                # Если URL не найден, создаем поисковую ссылку
                                                url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"

                                            product = {
                                                'name': title.strip(),
                                                'price': price.strip() if price else "Цена не указана",
                                                'url': url,
                                                'image': "",
                                                'description': f"Источник: Allegro, Релевантность: {score}",
                                                'relevance_score': score
                                            }
                                            products.append(product)
                                            logger.info(f"✅ Товар добавлен через резервный метод!")

                                except Exception as e:
                                    logger.debug(f"Ошибка обработки ссылки {i}: {e}")
                                    continue

                    except Exception as e:
                        logger.debug(f"Ошибка резервного поиска: {e}")

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
        # Создаем экземпляр скрапера
        scraper = AllegroScraper()

        # Сначала пробуем простой HTTP поиск
        logger.info(f"🔍 Попытка HTTP поиска на Allegro: {query}")
        http_results = scraper.search_products_simple(query)

        if http_results:
            logger.info(f"✅ HTTP поиск успешен: найдено {len(http_results)} товаров")
            return http_results

        logger.info("⚠️ HTTP поиск не дал результатов, пробуем Playwright...")

        # Если HTTP не сработал, пробуем Playwright (но с ограниченным временем)
        playwright_results = []
        try:
            playwright_results = asyncio.run(scraper.search_products(query))
            if playwright_results:
                logger.info(f"✅ Playwright поиск успешен: найдено {len(playwright_results)} товаров")
                return playwright_results
        except Exception as e:
            logger.error(f"❌ Ошибка Playwright поиска: {e}")

        # Если доступен AllegroParser с 2Captcha, пробуем его только если Playwright не дал результатов
        if AllegroParser and not playwright_results:
            logger.info("🚀 Пробуем AllegroParser с поддержкой 2captcha...")
            try:
                # Получаем API ключ для 2captcha
                import os
                captcha_api_key = os.getenv('CAPTCHA_API_KEY', '')

                # Создаем парсер
                parser = AllegroParser(captcha_api_key=captcha_api_key)

                # Выполняем поиск
                advanced_results = parser.search_allegro(query, limit=20, max_pages=max_pages)

                if advanced_results:
                    logger.info(f"✅ AllegroParser успешен: найдено {len(advanced_results)} товаров")
                    return advanced_results

            except Exception as e:
                logger.error(f"❌ Ошибка AllegroParser: {e}")

        # Если Playwright дал результаты, но мы их не вернули выше, возвращаем их сейчас
        if playwright_results:
            return playwright_results

        # Если ничего не сработало, возвращаем пустой список
        logger.warning("❌ Все методы поиска Allegro не сработали, товары не найдены")
        return []

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

    print(f"\n Найдено товаров: {len(results)}")
    for i, product in enumerate(results[:5]):
        print(f"{i+1}. {product['name'][:60]}...")
        print(f"   Цена: {product['price']}")
        print(f"   Релевантность: {product['relevance_score']}")
        print()

if __name__ == "__main__":
    asyncio.run(test_search())
