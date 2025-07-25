import asyncio
import logging
import httpx
import os
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page
import openai
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class AllegroScraper:
    def __init__(self):
        self.search_url = "https://allegro.pl/kategoria/komputery"
        self.captcha_api_key = os.getenv('2CAPTCHA_API_KEY', 'your_2captcha_api_key')

    def _use_mock_data(self) -> bool:
        """
        Возвращает True для использования mock данных
        """
        logger.info("Используем mock данные для демонстрации работы системы")
        return True

    def _get_mock_allegro_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Генерирует mock данные для Allegro
        """
        import random

        mock_products = []
        base_prices = [1299, 1899, 2499, 3199, 4299, 899, 1599, 2799]
        colors = ["Czarny", "Biały", "Niebieski", "Czerwony", "Zielony", "Srebrny"]
        brands = ["Samsung", "Apple", "Xiaomi", "Huawei", "Sony", "LG"]

        for i in range(10):
            price = base_prices[i % len(base_prices)] + random.randint(-200, 200)
            color = colors[i % len(colors)]
            brand = brands[i % len(brands)]

            mock_products.append({
                'name': f"{brand} {query.title()} {color} - Model {i+1}",
                'price': f"{price},00 zł",
                'url': f"https://allegro.pl/oferta/mock-{query}-{i+1}-{random.randint(10000, 99999)}",
                'image': f"https://via.placeholder.com/300x200/007bff/ffffff?text={query.title()}+{i+1}",
                'description': f"Продавец: MockStore, Рейтинг: 4.{random.randint(5, 9)}, Доставка: Darmowa dostawa"
            })

        logger.info(f"Сгенерировано {len(mock_products)} mock товаров для запроса '{query}'")
        return mock_products

    async def handle_gdpr_consent(self, page: Page) -> None:
        """
        Обрабатывает GDPR consent модальное окно
        """
        try:
            # Ждем появления GDPR модального окна
            gdpr_selectors = [
                '[data-role="accept-consent"]',
                'button:has-text("Akceptuję")',
                'button:has-text("Zgadzam się")',
                'button[id*="consent"]',
                'button[class*="consent"]',
                '#opbox-gdpr-consents-modal button',
                '[data-testid="consent-accept"]'
            ]

            for selector in gdpr_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0 and await element.first.is_visible():
                        logger.info(f"Найдено GDPR consent окно, кликаем: {selector}")
                        await element.first.click()
                        await asyncio.sleep(1)
                        return
                except Exception as e:
                    continue

            # Если не нашли кнопки согласия, пробуем закрыть модальное окно
            close_selectors = [
                'button[aria-label="Zamknij"]',
                'button:has-text("×")',
                '.modal-close',
                '[data-role="close"]'
            ]

            for selector in close_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0 and await element.first.is_visible():
                        logger.info(f"Закрываем модальное окно: {selector}")
                        await element.first.click()
                        await asyncio.sleep(1)
                        return
                except Exception as e:
                    continue

        except Exception as e:
            logger.warning(f"Не удалось обработать GDPR consent: {str(e)}")

    async def wait_and_handle_page_load(self, page: Page) -> None:
        """
        Ожидает загрузки страницы и обрабатывает возможные модальные окна
        """
        try:
            # Ждем загрузки страницы
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(2)

            # Обрабатываем GDPR consent
            await self.handle_gdpr_consent(page)

            # Дополнительная пауза после обработки модальных окон
            await asyncio.sleep(1)

        except Exception as e:
            logger.warning(f"Ошибка при ожидании загрузки страницы: {str(e)}")

    def calculate_relevance_score(self, title: str, query: str) -> int:
        """
        Улучшенная функция расчета релевантности товара
        """
        if not title or not query:
            return 0

        title_lower = title.lower()
        query_lower = query.lower()
        query_words = query_lower.split()
        title_words = title_lower.split()

        score = 0

        # 1. Проверка на точное совпадение всего запроса
        if query_lower in title_lower:
            score += 50

        # 2. Проверяем каждое слово из запроса
        for query_word in query_words:
            if len(query_word) >= 2:  # Игнорируем слишком короткие слова
                if query_word in title_lower:
                    if query_word in title_words:  # Точное совпадение слова
                        score += len(query_word) * 10
                    else:  # Частичное совпадение (слово содержится в другом слове)
                        score += len(query_word) * 5

        # 3. Бонусы за ключевые слова (специфично для товаров)
        key_terms = {
            'macbook': 30,
            'mac': 25,
            'apple': 20,
            'iphone': 30,
            'samsung': 25,
            'xiaomi': 25,
            'huawei': 20,
            'laptop': 15,
            'notebook': 15,
            'pro': 10,
            'max': 10,
            'plus': 8,
            'm4': 25,
            'm3': 20,
            'm2': 15,
            'm1': 10,
            'air': 15,
            'mini': 10
        }

        for term, bonus in key_terms.items():
            if term in title_lower:
                score += bonus

        # 4. Штрафы за нерелевантные слова
        irrelevant_terms = [
            'case', 'obudowa', 'cover', 'pokrowiec', 'kabel', 'cable',
            'ładowarka', 'charger', 'adapter', 'mouse', 'mysz', 'keyboard',
            'klawiatura', 'stand', 'podstawka', 'bag', 'torba', 'screen',
            'folia', 'protector', 'szkło', 'glass'
        ]

        for term in irrelevant_terms:
            if term in title_lower:
                score -= 20

        # 5. Бонус за наличие цены (индикатор того, что это реальный товар)
        # Это будет проверяться в основной функции

        return max(0, score)  # Минимальный скор = 0

    async def search_allegro_playwright(self, query: str, max_pages: int = 3, debug_mode: bool = False) -> List[Dict[str, Any]]:
        """
        Выполняет поиск товаров на Allegro через Playwright
        """
        products = []

        try:
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding'
                    ]
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                )

                page = await context.new_page()

                # Переходим на страницу поиска
                search_url = f"https://allegro.pl/listing?string={query.replace(' ', '+')}"
                logger.info(f"Переходим на: {search_url}")

                await page.goto(search_url, wait_until="networkidle", timeout=30000)

                # Ждем и обрабатываем загрузку страницы
                await self.wait_and_handle_page_load(page)

                # Проверяем на капчу
                page_content = await page.content()
                if "captcha" in page_content.lower() or "recaptcha" in page_content.lower():
                    logger.warning("Обнаружена капча, но продолжаем парсинг...")

                # Парсим страницы
                for page_num in range(1, max_pages + 1):
                    logger.info(f"Парсим страницу {page_num}")

                    # Ждем загрузки товаров с несколькими селекторами
                    product_selectors = [
                        '[data-role="offer"]',
                        '.opbox-listing',
                        'article[data-analytics-view-label]',
                        '.offer',
                        '[data-testid="listing-item"]',
                        'div[data-testid="web-listing-item"]'
                    ]

                    products_found = False
                    for selector in product_selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=10000)
                            products_found = True
                            logger.info(f"Найдены товары с селектором: {selector}")
                            break
                        except:
                            continue

                    if not products_found:
                        logger.warning(f"Товары не найдены на странице {page_num}")
                        if page_num == 1:
                            # Если на первой странице ничего не найдено, пробуем другие селекторы
                            logger.info("Пробуем альтернативные селекторы...")
                            await asyncio.sleep(3)
                            continue
                        else:
                            break

                    # Получаем карточки товаров с расширенным списком селекторов
                    cards_locator = page.locator(', '.join(product_selectors))
                    cards_count = await cards_locator.count()

                    logger.info(f"Found {cards_count} products on page {page_num}")

                    if cards_count == 0:
                        logger.warning(f"Карточки товаров не найдены на странице {page_num}")
                        if page_num == 1:
                            break
                        else:
                            continue

                    # Парсим каждую карточку
                    page_products = 0
                    for i in range(cards_count):
                        try:
                            card = cards_locator.nth(i)

                            # Получаем реальные данные карточки с расширенными селекторами
                            product_data = await card.evaluate("""
                                (element) => {
                                    const data = {};
                                    
                                    // Название товара - расширенный список селекторов
                                    const titleSelectors = [
                                        '[data-role="title"]',
                                        'h2 a',
                                        'h3 a',
                                        'h2',
                                        'h3',
                                        '.opbox-listing-title',
                                        '[data-testid="listing-title"]',
                                        'a[href*="/oferta/"]',
                                        '.offer-title',
                                        'a[title]'
                                    ];
                                    
                                    let titleEl = null;
                                    let titleText = '';
                                    for (const selector of titleSelectors) {
                                        titleEl = element.querySelector(selector);
                                        if (titleEl) {
                                            titleText = titleEl.textContent?.trim() || titleEl.title?.trim() || '';
                                            if (titleText) break;
                                        }
                                    }
                                    data.title = titleText;
                                    
                                    // Цена - расширенный список селекторов
                                    const priceSelectors = [
                                        '[data-role="price"]',
                                        '.opbox-listing-price',
                                        '.price',
                                        '[data-testid="price"]',
                                        '.offer-price',
                                        '.price-value',
                                        'span[class*="price"]',
                                        'div[class*="price"]'
                                    ];
                                    
                                    let priceEl = null;
                                    let priceText = '';
                                    for (const selector of priceSelectors) {
                                        priceEl = element.querySelector(selector);
                                        if (priceEl) {
                                            priceText = priceEl.textContent?.trim() || '';
                                            if (priceText && (priceText.includes('zł') || priceText.includes(','))) break;
                                        }
                                    }
                                    data.price = priceText;
                                    
                                    // Ссылка
                                    const linkEl = element.querySelector('a[href*="/oferta/"]') || 
                                                  element.querySelector('a[href*="allegro.pl"]');
                                    data.url = linkEl ? linkEl.href : '';
                                    
                                    // Изображение
                                    const imgEl = element.querySelector('img');
                                    data.image = imgEl ? (imgEl.src || imgEl.dataset.src || imgEl.dataset.original) : '';
                                    
                                    // Продавец
                                    const sellerSelectors = [
                                        '[data-role="seller"]',
                                        '.seller-name',
                                        '.offer-seller',
                                        '[data-testid="seller-name"]',
                                        'span[class*="seller"]'
                                    ];
                                    
                                    let sellerEl = null;
                                    for (const selector of sellerSelectors) {
                                        sellerEl = element.querySelector(selector);
                                        if (sellerEl && sellerEl.textContent?.trim()) break;
                                    }
                                    data.seller = sellerEl ? sellerEl.textContent.trim() : '';
                                    
                                    return data;
                                }
                            """)

                            # Логируем найденные данные
                            if debug_mode:
                                logger.info(f"Карточка {i}: title='{product_data.get('title', '')[:60]}...', price='{product_data.get('price', '')}'")

                            # Проверяем что у нас есть основные данные
                            title = product_data.get('title', '').strip()
                            price = product_data.get('price', '').strip()

                            if title and price:
                                # Вычисляем релевантность
                                score = self.calculate_relevance_score(title, query)

                                # Более мягкие критерии фильтрации
                                min_score = 10 if not debug_mode else 0

                                # Проверяем релевантность
                                is_relevant = score >= min_score

                                # Дополнительная проверка для товаров с очень низким скором но потенциально релевантных
                                if not is_relevant and score > 0:
                                    query_words = query.lower().split()
                                    title_lower = title.lower()
                                    # Если хотя бы одно важное слово из запроса присутствует
                                    important_words = [word for word in query_words if len(word) >= 3]
                                    if any(word in title_lower for word in important_words):
                                        is_relevant = True
                                        score += 5  # Небольшой бонус

                                if is_relevant or debug_mode:
                                    formatted_product = {
                                        'name': title,
                                        'price': price,
                                        'url': product_data.get('url', ''),
                                        'image': product_data.get('image', ''),
                                        'description': f"Продавец: {product_data.get('seller', 'N/A')}, Источник: Allegro",
                                        'relevance_score': score
                                    }

                                    products.append(formatted_product)
                                    logger.info(f"✅ ДОБАВЛЕН товар: {title[:50]}... (Score: {score})")
                                    page_products += 1
                                else:
                                    logger.debug(f"❌ Пропущен товар: {title[:50]}... (Score: {score})")
                            else:
                                if debug_mode:
                                    logger.debug(f"Карточка без названия или цены: title='{title}', price='{price}'")

                        except Exception as e:
                            logger.error(f"Ошибка при парсинге карточки {i}: {str(e)}")

                    logger.info(f"✅ Добавлено {page_products} товаров со страницы {page_num}")

                    # Если на первой странице найдены релевантные товары, можно продолжить
                    if page_num == 1 and page_products > 0:
                        logger.info(f"Найдено {page_products} релевантных товаров на первой странице")

                    # Переходим на следующую страницу
                    if page_num < max_pages and page_products > 0:  # Переходим только если нашли товары
                        try:
                            await self.handle_gdpr_consent(page)

                            # Расширенные селекторы для кнопки "Следующая"
                            next_selectors = [
                                'a[aria-label="Następna"]',
                                'a:has-text("Następna")',
                                'button:has-text("Następna")',
                                'a[rel="next"]',
                                '[data-role="next-page"]',
                                '.pagination-next',
                                'a[data-page]',
                                'a[title*="następn"]'
                            ]

                            next_button = None
                            for selector in next_selectors:
                                try:
                                    locator = page.locator(selector)
                                    if await locator.count() > 0:
                                        next_button = locator.first
                                        break
                                except:
                                    continue

                            if next_button:
                                # Прокручиваем к кнопке
                                await next_button.scroll_into_view_if_needed()
                                await asyncio.sleep(1)

                                # Пробуем разные способы клика
                                try:
                                    await next_button.click(timeout=5000)
                                except Exception as e1:
                                    try:
                                        logger.warning("Обычный клик не сработал, пробуем force клик")
                                        await next_button.click(force=True, timeout=5000)
                                    except Exception as e2:
                                        try:
                                            logger.warning("Force клик не сработал, используем JavaScript")
                                            await next_button.evaluate("element => element.click()")
                                        except Exception as e3:
                                            logger.error(f"Все способы клика не сработали: {str(e3)}")
                                            break

                                # Ждем загрузки новой страницы
                                await self.wait_and_handle_page_load(page)

                            else:
                                logger.info("Следующая страница не найдена")
                                break

                        except Exception as e:
                            logger.error(f"Ошибка при переходе на следующую страницу: {str(e)}")
                            break
                    elif page_products == 0:
                        logger.info("На странице не найдено релевантных товаров, останавливаем поиск")
                        break

                await browser.close()

        except Exception as e:
            logger.error(f"Ошибка при поиске на Allegro: {str(e)}")

        # Сортируем по релевантности
        products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        logger.info(f"🎯 ИТОГО найдено товаров на Allegro: {len(products)}")
        if len(products) > 0:
            logger.info("📋 Топ-5 найденных товаров:")
            for i, product in enumerate(products[:5]):
                logger.info(f"  {i+1}. {product['name'][:60]}... (Score: {product.get('relevance_score', 0)})")
        else:
            logger.warning("⚠️  НЕ НАЙДЕНО НИ ОДНОГО РЕЛЕВАНТНОГО ТОВАРА!")

        return products

# Синхронная обертка для совместимости с существующим кодом
def search_allegro_improved(query: str, max_pages: int = 3, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Синхронная обертка для асинхронной функции поиска
    """
    try:
        return asyncio.run(AllegroScraper().search_allegro_playwright(query, max_pages, debug_mode))
    except Exception as e:
        logger.error(f"Ошибка в search_allegro_improved: {str(e)}")
        return []

def generate_allegro_listing_template(product_data: Dict[str, Any], use_openai: bool = False) -> Dict[str, Any]:
    # Извлекаем название товара
    product_name = product_data.get('name', '')
    price = product_data.get('price', '')

    # Генерируем описание
    if use_openai:
        description = generate_openai_description(product_name, price)
        parameters = generate_openai_parameters(product_name)
        tags = generate_openai_tags(product_name)
    else:
        description = generate_product_description(product_name, price)
        parameters = generate_product_parameters(product_name)
        tags = generate_tags(product_name)

    # Создаем шаблон объявления
    listing_template = {
        'title': product_name,
        'price': price,
        'description': description,
        'parameters': parameters,
        'images': [product_data.get('image', '')],
        'category': determine_category(product_name),
        'condition': 'Nowy',  # Новый товар
        'warranty': 'Gwarancja producenta',
        'shipping': 'Darmowa dostawa',
        'payment': 'Przelew online, Pobranie',
        'tags': tags,
        'highlights': generate_highlights(product_name),
        'features': generate_features(product_name),
        'generated_with_openai': use_openai
    }

    return listing_template

def generate_product_description(product_name: str, price: str) -> str:
    """
    Генерирует описание товара на основе его названия
    """
    name_lower = product_name.lower()

    # Базовое описание
    base_description = f"{product_name}\n\n"

    # Добавляем специфичные описания в зависимости от типа товара
    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi', 'huawei']):
        base_description += """✅ Wysokiej Jakości Smartfon

Idealny telefon komórkowy z najnowszymi funkcjami i technologią. Doskonały wybór dla osób poszukujących niezawodnego urządzenia mobilnego.

✅ Kluczowe Funkcje:
• Najnowszy system operacyjny
• Wysokiej jakości aparat fotograficzny
• Szybkie ładowanie
• Długa żywotność baterii
• Bezpieczne uwierzytelnianie

✅ Idealny dla:
• Codziennego użytku
• Robienia zdjęć i filmów
• Przeglądania internetu
• Gier mobilnych
• Pracy i rozrywki

✅ Gwarancja i Wsparcie:
• Pełna gwarancja producenta
• Profesjonalne wsparcie techniczne
• Bezpieczne zakupy online

Zamów teraz i ciesz się najwyższą jakością! 🚀"""

    elif any(word in name_lower for word in ['macbook', 'laptop', 'notebook']):
        base_description += """✅ Profesjonalny Laptop

Wydajny komputer przenośny idealny do pracy, nauki i rozrywki. Najnowsze komponenty zapewniają płynne działanie wszystkich aplikacji.

✅ Specyfikacja Techniczna:
• Najnowszy procesor
• Szybka pamięć RAM
• Pojemny dysk SSD
• Wysokiej jakości ekran
• Długa żywotność baterii

✅ Idealny dla:
• Pracy biurowej
• Projektów graficznych
• Programowania
• Nauki zdalnej
• Rozrywki multimedialnej

✅ Dodatkowe Korzyści:
• Lekka i kompaktowa konstrukcja
• Szybkie uruchamianie
• Cicha praca
• Profesjonalny wygląd

Zamów teraz i zwiększ swoją produktywność! 💻"""

    elif any(word in name_lower for word in ['kamera', 'aparat', 'camera']):
        base_description += """✅ Profesjonalny Aparat Fotograficzny

Wysokiej jakości aparat cyfrowy idealny dla miłośników fotografii. Zaawansowane funkcje pozwalają na tworzenie wspaniałych zdjęć.

✅ Kluczowe Funkcje:
• Wysoka rozdzielczość zdjęć
• Zaawansowany zoom optyczny
• Stabilizacja obrazu
• Intuicyjne menu
• Długa żywotność baterii

✅ Idealny dla:
• Fotografii amatorskiej
• Podróży i wycieczek
• Dokumentowania ważnych chwil
• Rozwoju pasji fotograficznej
• Profesjonalnych projektów

✅ Dodatkowe Korzyści:
• Kompaktowy rozmiar
• Łatwa obsługa
• Wysokiej jakości materiały
• Kompletne wyposażenie

Zamów teraz i uchwyć piękne chwile! 📸"""

    else:
        # Общее описание для других товаров
        base_description += """✅ Wysokiej Jakości Produkt

Profesjonalny produkt najwyższej jakości, który spełni wszystkie Twoje oczekiwania. Idealny wybór dla wymagających klientów.

✅ Kluczowe Zalety:
• Najwyższa jakość wykonania
• Sprawdzone materiały
• Długoletnia gwarancja
• Profesjonalne wsparcie
• Szybka dostawa

✅ Idealny dla:
• Codziennego użytku
• Profesjonalnych zastosowań
• Prezentów dla bliskich
• Rozwoju pasji i hobby
• Zwiększenia komfortu życia

✅ Dodatkowe Korzyści:
• Bezpieczne zakupy
• Darmowa dostawa
• Elastyczne metody płatności
• Pełne wsparcie klienta

Zamów teraz i ciesz się najwyższą jakością! ⭐"""

    return base_description

def generate_product_parameters(product_name: str) -> Dict[str, str]:
    """
    Генерирует параметры товара на основе названия
    """
    name_lower = product_name.lower()
    parameters = {
        'Stan': 'Nowy',
        'Faktura': 'Wystawiam fakturę VAT',
        'Marka': 'Oryginalna'
    }
    """
    Генерирует описание товара на основе его названия
    """
    name_lower = product_name.lower()

    # Базовое описание
    base_description = f"{product_name}\n\n"

    # Добавляем специфичные описания в зависимости от типа товара
    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi', 'huawei']):
        base_description += """✅ Wysokiej Jakości Smartfon

Idealny telefon komórkowy z najnowszymi funkcjami i technologią. Doskonały wybór dla osób poszukujących niezawodnego urządzenia mobilnego.

✅ Kluczowe Funkcje:
• Najnowszy system operacyjny
• Wysokiej jakości aparat fotograficzny
• Szybkie ładowanie
• Długa żywotność baterii
• Bezpieczne uwierzytelnianie

✅ Idealny dla:
• Codziennego użytku
• Robienia zdjęć i filmów
• Przeglądania internetu
• Gier mobilnych
• Pracy i rozrywki

✅ Gwarancja i Wsparcie:
• Pełna gwarancja producenta
• Profesjonalne wsparcie techniczne
• Bezpieczne zakupy online

Zamów teraz i ciesz się najwyższą jakością! 🚀"""

    elif any(word in name_lower for word in ['macbook', 'laptop', 'notebook']):
        base_description += """✅ Profesjonalny Laptop

Wydajny komputer przenośny idealny do pracy, nauki i rozrywki. Najnowsze komponenty zapewniają płynne działanie wszystkich aplikacji.

✅ Specyfikacja Techniczna:
• Najnowszy procesor
• Szybka pamięć RAM
• Pojemny dysk SSD
• Wysokiej jakości ekran
• Długa żywotność baterii

✅ Idealny dla:
• Pracy biurowej
• Projektów graficznych
• Programowania
• Nauki zdalnej
• Rozrywki multimedialnej

✅ Dodatkowe Korzyści:
• Lekka i kompaktowa konstrukcja
• Szybkie uruchamianie
• Cicha praca
• Profesjonalny wygląd

Zamów teraz i zwiększ swoją produktywność! 💻"""

    elif any(word in name_lower for word in ['kamera', 'aparat', 'camera']):
        base_description += """✅ Profesjonalny Aparat Fotograficzny

Wysokiej jakości aparat cyfrowy idealny dla miłośników fotografii. Zaawansowane funkcje pozwalają na tworzenie wspaniałych zdjęć.

✅ Kluczowe Funkcje:
• Wysoka rozdzielczość zdjęć
• Zaawansowany zoom optyczny
• Stabilizacja obrazu
• Intuicyjne menu
• Długa żywotność baterii

✅ Idealny dla:
• Fotografii amatorskiej
• Podróży i wycieczek
• Dokumentowania ważnych chwil
• Rozwoju pasji fotograficznej
• Profesjonalnych projektów

✅ Dodatkowe Korzyści:
• Kompaktowy rozmiar
• Łatwa obsługa
• Wysokiej jakości materiały
• Kompletne wyposażenie

Zamów teraz i uchwyć piękne chwile! 📸"""

    else:
        # Общее описание для других товаров
        base_description += """✅ Wysokiej Jakości Produkt

Profesjonalny produkt najwyższej jakości, który spełni wszystkie Twoje oczekiwania. Idealny wybór dla wymagających klientów.

✅ Kluczowe Zalety:
• Najwyższa jakość wykonania
• Sprawdzone materiały
• Długoletnia gwarancja
• Profesjonalne wsparcie
• Szybka dostawa

✅ Idealny dla:
• Codziennego użytku
• Profesjonalnych zastosowań
• Prezentów dla bliskich
• Rozwoju pasji i hobby
• Zwiększenia komfortu życia

✅ Dodatkowe Korzyści:
• Bezpieczne zakupy
• Darmowa dostawa
• Elastyczne metody płatności
• Pełne wsparcie klienta

Zamów teraz i ciesz się najwyższą jakością! ⭐"""

    return base_description

def generate_product_parameters(product_name: str) -> Dict[str, str]:
    """
    Генерирует параметры товара на основе названия
    """
    name_lower = product_name.lower()
    parameters = {
        'Stan': 'Nowy',
        'Faktura': 'Wystawiam fakturę VAT',
        'Marka': 'Oryginalna'
    }

    # Добавляем специфичные параметры
    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi']):
        parameters.update({
            'Typ': 'Smartfon',
            'System operacyjny': 'Android/iOS',
            'Pamięć RAM': '4GB+',
            'Pojemność': '128GB+',
            'Aparat': 'Wielokrotny'
        })
    elif any(word in name_lower for word in ['macbook', 'laptop']):
        parameters.update({
            'Typ': 'Laptop',
            'Procesor': 'Intel/Apple Silicon',
            'Pamięć RAM': '8GB+',
            'Dysk': 'SSD 256GB+',
            'Ekran': '13"+'
        })
    elif any(word in name_lower for word in ['kamera', 'aparat']):
        parameters.update({
            'Typ': 'Aparat cyfrowy',
            'Rozdzielczość': '12MP+',
            'Zoom': '16x+',
            'Ekran': '2.4"+',
            'Pamięć': 'Wbudowana + karta SD'
        })

    return parameters

def determine_category(product_name: str) -> str:
    """
    Определяет категорию товара на основе названия
    """
    name_lower = product_name.lower()

    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi', 'huawei', 'telefon']):
        return 'Telefony i Akcesoria'
    elif any(word in name_lower for word in ['macbook', 'laptop', 'notebook', 'komputer']):
        return 'Komputery'
    elif any(word in name_lower for word in ['kamera', 'aparat', 'camera']):
        return 'Fotografia'
    elif any(word in name_lower for word in ['słuchawki', 'headphones']):
        return 'Audio i Hi-Fi'
    else:
        return 'Elektronika'

def generate_tags(product_name: str) -> List[str]:
    """
    Генерирует теги для товара
    """
    name_lower = product_name.lower()
    tags = ['nowy', 'oryginalny', 'gwarancja', 'dostawa']

    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi']):
        tags.extend(['smartfon', 'telefon', 'mobilny', 'android', 'ios'])
    elif any(word in name_lower for word in ['macbook', 'laptop']):
        tags.extend(['laptop', 'komputer', 'przenośny', 'macos', 'windows'])
    elif any(word in name_lower for word in ['kamera', 'aparat']):
        tags.extend(['fotografia', 'aparat', 'cyfrowy', 'zoom'])

    return tags

def generate_highlights(product_name: str) -> List[str]:
    """
    Генерирует основные преимущества товара
    """
    name_lower = product_name.lower()
    highlights = ['✅ Nowy produkt', '✅ Pełna gwarancja', '✅ Darmowa dostawa']

    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi']):
        highlights.extend([
            '✅ Najnowszy model',
            '✅ Wysokiej jakości aparat',
            '✅ Długa żywotność baterii'
        ])
    elif any(word in name_lower for word in ['macbook', 'laptop']):
        highlights.extend([
            '✅ Wydajny procesor',
            '✅ Szybki dysk SSD',
            '✅ Wysokiej jakości ekran'
        ])
    elif any(word in name_lower for word in ['kamera', 'aparat']):
        highlights.extend([
            '✅ Wysoka rozdzielczość',
            '✅ Zaawansowany zoom',
            '✅ Stabilizacja obrazu'
        ])

    return highlights

def generate_features(product_name: str) -> List[str]:
    """
    Генерирует список функций товара
    """
    name_lower = product_name.lower()
    features = ['Oryginalny produkt', 'Pełna gwarancja', 'Bezpieczne zakupy']

    if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi']):
        features.extend([
            'Najnowszy system operacyjny',
            'Wielokrotny aparat fotograficzny',
            'Szybkie ładowanie',
            'Bezpieczne uwierzytelnianie',
            'Wodoodporność'
        ])
    elif any(word in name_lower for word in ['macbook', 'laptop']):
        features.extend([
            'Najnowszy procesor',
            'Szybka pamięć RAM',
            'Pojemny dysk SSD',
            'Wysokiej jakości ekran',
            'Długa żywotność baterii'
        ])
    elif any(word in name_lower for word in ['kamera', 'aparat']):
        features.extend([
            'Wysoka rozdzielczość zdjęć',
            'Zaawansowany zoom optyczny',
            'Stabilizacja obrazu',
            'Intuicyjne menu',
            'Kompaktowy rozmiar'
        ])

    return features

# Функция для создания полного шаблона объявления
def create_full_allegro_listing(product_data: Dict[str, Any], use_openai: bool = False) -> Dict[str, Any]:
    """
    Создает полный шаблон объявления для Allegro

    Args:
        product_data: Данные товара
        use_openai: Использовать ли OpenAI для генерации
    """
    template = generate_allegro_listing_template(product_data, use_openai)

    # Добавляем дополнительную информацию
    template['additional_info'] = {
        'shipping_time': '1-3 dni robocze',
        'return_policy': '14 dni na zwrot',
        'warranty_period': '24 miesiące',
        'payment_methods': ['Przelew online', 'Pobranie', 'PayU', 'BLIK'],
        'contact_info': {
            'phone': '+48 XXX XXX XXX',
            'email': 'kontakt@sklep.pl',
            'support_hours': 'Pon-Pt 9:00-17:00'
        }
    }

    return template

def generate_openai_description(product_name: str, price: str, product_type: str = None) -> str:
    """
    Генерирует описание товара с помощью OpenAI API
    """
    try:
        if not openai.api_key:
            logger.warning("OpenAI API key not found, using fallback description")
            return generate_product_description(product_name, price)

        # Определяем тип товара если не указан
        if not product_type:
            name_lower = product_name.lower()
            if any(word in name_lower for word in ['iphone', 'samsung', 'xiaomi', 'huawei']):
                product_type = 'smartphone'
            elif any(word in name_lower for word in ['macbook', 'laptop', 'notebook']):
                product_type = 'laptop'
            elif any(word in name_lower for word in ['kamera', 'aparat', 'camera']):
                product_type = 'camera'
            else:
                product_type = 'electronics'

        # Создаем промпт для OpenAI
        prompt = f"""
        Stwórz profesjonalny opis produktu dla Allegro w języku polskim.
        
        Nazwa produktu: {product_name}
        Cena: {price}
        Typ produktu: {product_type}
        
        Opis powinien zawierać:
        1. Krótkie wprowadzenie o produkcie
        2. Kluczowe funkcje i zalety (z emoji ✅)
        3. Dla kogo jest idealny (z emoji 🎯)
        4. Dodatkowe korzyści (z emoji ⭐)
        5. Zachęcające zakończenie z call-to-action
        
        Opis powinien być:
        - Napisany w języku polskim
        - Zawierać emoji dla lepszej czytelności
        - Być zachęcający do zakupu
        - Zawierać około 200-300 słów
        - Używać profesjonalnego ale przyjaznego tonu
        
        Format:
        [Nazwa produktu]
        
        [Wprowadzenie]
        
        ✅ Kluczowe Funkcje:
        • [funkcja 1]
        • [funkcja 2]
        • [funkcja 3]
        
        🎯 Idealny dla:
        • [grupa docelowa 1]
        • [grupa docelowa 2]
        • [grupa docelowa 3]
        
        ⭐ Dodatkowe Korzyści:
        • [korzyść 1]
        • [korzyść 2]
        • [korzyść 3]
        
        [Zachęcające zakończenie z call-to-action]
        """

        # Вызываем OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w tworzeniu opisów produktów dla platformy Allegro. Tworzysz profesjonalne, zachęcające opisy w języku polskim."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        description = response.choices[0].message.content.strip()
        logger.info(f"OpenAI description generated for: {product_name[:50]}...")

        return description

    except Exception as e:
        logger.error(f"Error generating OpenAI description: {str(e)}")
        # Возвращаем fallback описание
        return generate_product_description(product_name, price)

def generate_openai_parameters(product_name: str) -> Dict[str, str]:
    """
    Генерирует параметры товара с помощью OpenAI API
    """
    try:
        if not openai.api_key:
            logger.warning("OpenAI API key not found, using fallback parameters")
            return generate_product_parameters(product_name)

        prompt = f"""
        Stwórz listę parametrów technicznych dla produktu na Allegro w formacie JSON.
        
        Nazwa produktu: {product_name}
        
        Zwróć JSON z parametrami w formacie:
        {{
            "Stan": "Nowy",
            "Faktura": "Wystawiam fakturę VAT",
            "Marka": "[marka]",
            "Typ": "[typ produktu]",
            "parametr1": "wartość1",
            "parametr2": "wartość2"
        }}
        
        Parametry powinny być:
        - Odpowiednie dla typu produktu
        - Napisane w języku polskim
        - Realistyczne i profesjonalne
        - Zawierać 5-8 parametrów
        
        Zwróć tylko JSON, bez dodatkowego tekstu.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w specyfikacjach technicznych produktów. Zwracasz tylko JSON z parametrami."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )

        import json
        parameters_text = response.choices[0].message.content.strip()
        parameters = json.loads(parameters_text)

        logger.info(f"OpenAI parameters generated for: {product_name[:50]}...")
        return parameters

    except Exception as e:
        logger.error(f"Error generating OpenAI parameters: {str(e)}")
        return generate_product_parameters(product_name)

def generate_openai_tags(product_name: str) -> List[str]:
    """
    Генерирует теги для товара с помощью OpenAI API
    """
    try:
        if not openai.api_key:
            logger.warning("OpenAI API key not found, using fallback tags")
            return generate_tags(product_name)

        prompt = f"""
        Stwórz listę tagów (słów kluczowych) dla produktu na Allegro.
        
        Nazwa produktu: {product_name}
        
        Zwróć listę 8-12 tagów w formacie JSON:
        ["tag1", "tag2", "tag3", ...]
        
        Tagi powinny być:
        - W języku polskim
        - Odpowiednie dla wyszukiwania
        - Zawierać różne aspekty produktu
        - Być popularne w wyszukiwaniach
        
        Zwróć tylko JSON array, bez dodatkowego tekstu.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem w SEO i słowach kluczowych. Zwracasz tylko JSON array z tagami."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.5
        )

        import json
        tags_text = response.choices[0].message.content.strip()
        tags = json.loads(tags_text)

        logger.info(f"OpenAI tags generated for: {product_name[:50]}...")
        return tags

    except Exception as e:
        logger.error(f"Error generating OpenAI tags: {str(e)}")
        return generate_tags(product_name)

# Тестовая функция
async def test_allegro_search():
    """
    Тестирует поиск на Allegro
    """
    scraper = AllegroScraper()
    results = await scraper.search_allegro_playwright("iphone", max_pages=1)
    print(f"Найдено товаров: {len(results)}")
    for i, product in enumerate(results[:3]):
        print(f"{i+1}. {product['name']} - {product['price']}")

if __name__ == "__main__":
    asyncio.run(test_allegro_search())