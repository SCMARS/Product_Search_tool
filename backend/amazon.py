import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import os
from urllib.parse import urlencode, quote_plus
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def matches_query(product_name, query, min_score=30):
    """
    Улучшенная функция проверки релевантности товара
    """
    if not product_name or not query:
        return 0.0

    product_lower = product_name.lower()
    query_lower = query.lower()

    # Разбиваем запрос на слова
    query_words = query_lower.split()

    # Базовый счет - количество совпадающих слов
    score = 0
    matched_words = 0

    # СУПЕР БОНУС за точное совпадение всей фразы
    if query_lower in product_lower:
        score += 200  # Максимальный бонус за точное совпадение
        logger.debug(f"🎯 ТОЧНОЕ СОВПАДЕНИЕ: '{query_lower}' в '{product_lower}'")

    # Проверяем каждое слово из запроса
    for word in query_words:
        if len(word) > 1 and word in product_lower:  # Учитываем даже короткие важные слова
            if len(word) <= 2:
                score += 15   # Маленький бонус за короткие слова (11, 16, pro)
            elif len(word) <= 4:
                score += 30  # Средний бонус за средние слова (ipad, pro)
            else:
                score += 40  # Большой бонус за длинные слова
            matched_words += 1

    if len(query_words) > 0:
        match_percentage = matched_words / len(query_words)
        score += int(match_percentage * 60)  # До 60 дополнительных баллов

    # ОГРОМНЫЙ бонус за точное совпадение бренда в начале названия
    if len(query_words) >= 1:
        brand = query_words[0]  # Первое слово как бренд
        if product_lower.startswith(brand.lower()) or f" {brand.lower()} " in product_lower:
            score += 100  # Большой бонус за правильный бренд

    # Проверяем фразы из 2 слов
    for i in range(len(query_words) - 1):
        phrase = f"{query_words[i]} {query_words[i+1]}"
        if len(phrase) > 3 and phrase in product_lower:  # Минимум 3 символа
            score += 50  # Бонус за фразу из 2 слов

    # Проверяем фразы из 3 слов
    for i in range(len(query_words) - 2):
        phrase = f"{query_words[i]} {query_words[i+1]} {query_words[i+2]}"
        if phrase in product_lower:
            score += 80  # Больший бонус за фразу из 3 слов

    # Проверяем фразы из 4+ слов
    for i in range(len(query_words) - 3):
        phrase = " ".join(query_words[i:i+4])
        if phrase in product_lower:
            score += 120  # Максимальный бонус за длинную фразу

    # Дополнительный бонус за точное совпадение всего запроса
    if query_lower in product_lower:
        score += 80

    # Специальная обработка для SKIRCO и подобных товаров
    if 'skirco' in query_lower or 'skir\'co' in query_lower:
        # Если ищем SKIRCO, то любой товар с SKIRCO должен проходить
        if 'skirco' in product_lower or 'skir\'co' in product_lower:
            score += 150  # Большой бонус за SKIRCO
            logger.debug(f"🎯 SKIRCO товар найден: {product_name}")

    # Строгая проверка: если товар содержит слова аксессуаров, то он НЕ является смартфоном
    accessory_strict_keywords = ['hülle', 'case', 'cover', 'schutz', 'protection', 'folie', 'screen protector', 
                               'panzerglas', 'powerbank', 'charger', 'ladegerät', 'kabel', 'cable', 'adapter',
                               'stück', 'pack', 'set', 'kit', 'zubehör', 'accessory', 'protector', 'guard',
                               'displayschutz', 'kamera', 'camera', 'schutzglas', 'protection glass']
    
    # Только для iPhone запросов применяем фильтр аксессуаров
    if 'iphone' in query_lower and any(keyword in product_lower for keyword in accessory_strict_keywords):
        # Если товар содержит слова аксессуаров, то он НЕ является смартфоном
        return 0.0  # Полностью исключаем из результатов

    # Специальные правила для iPhone
    if 'iphone' in query_lower:
        # Бонус за точную модель iPhone
        if '16' in query_lower and '16' in product_lower:
            score += 60
        if 'pro' in query_lower and 'pro' in product_lower:
            score += 50
        if 'max' in query_lower and 'max' in product_lower:
            score += 50
        
        # Бонус за товары, которые точно являются смартфонами
        phone_keywords = ['gb', 'tb', 'handy', 'smartphone', 'mobile', 'telefon', 'phone']
        if any(keyword in product_lower for keyword in phone_keywords):
            score += 40  # Бонус за смартфон

        return float(score)
    
    # Возвращаем финальный счет для всех остальных случаев
    return float(score)

def search_amazon(query, limit=50, max_pages=1):
    """
    Поиск товаров на Amazon.de - ВСЕ НАЙДЕННЫЕ ТОВАРЫ
    """
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Referer': 'https://www.amazon.de/'
        }
        
        # ТОЛЬКО ПЕРВАЯ СТРАНИЦА
        page = 1
        logger.info(f"Searching page {page}...")

        # Используем более простой URL
        url = f"https://www.amazon.de/s?k={quote_plus(query)}"
        logger.info(f"🔍 Amazon URL: {url}")

        # Добавляем задержку перед запросом
        time.sleep(2)
        
        response = requests.get(url, headers=headers, timeout=20)
        
        logger.info(f"📡 Amazon response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ Amazon вернул ошибку {response.status_code}")
            return results

        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем товары на странице - используем более широкие селекторы
        products = []
        
        # Попробуем разные селекторы для поиска товаров
        selectors = [
            'div[data-component-type="s-search-result"]',
            'div.s-result-item',
            'div[data-asin]',
            'div.a-section.a-spacing-base',
            'div[class*="s-result-item"]',
            'div[data-component-type="s-search-result"]'
        ]
        
        for selector in selectors:
            products = soup.select(selector)
            if products:
                logger.info(f"Found {len(products)} products with selector: {selector}")
                break

        if not products:
            logger.warning("No products found with any selector")
            # Попробуем найти любые товары
            products = soup.find_all('div', {'data-asin': True})
            if products:
                logger.info(f"Found {len(products)} products with data-asin")
            else:
                logger.warning("No products found at all")
                return results

        logger.info(f"🔍 Обрабатываем {len(products)} товаров...")

        for i, product in enumerate(products):
            if len(results) >= limit:
                break

            try:
                # Название товара - улучшенный поиск
                title = None
                title_selectors = [
                    'h2 a span',
                    'h2 span',
                    'h2 a',
                    'h2',
                    '.a-size-medium',
                    '.a-size-mini',
                    'a[data-cy="title-recipe-link"]',
                    'a[href*="/dp/"] span',
                    'span[data-cy="title-recipe-collection"]',
                    'a[href*="/dp/"]',
                    'span.a-size-base-plus',
                    'span.a-size-mini'
                ]

                for selector in title_selectors:
                    title_elem = product.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 5:
                            break

                if not title:
                    logger.debug(f"❌ Не найдено название для товара {i}")
                    continue

                # УБИРАЕМ ФИЛЬТР РЕЛЕВАНТНОСТИ - ВОЗВРАЩАЕМ ВСЕ ТОВАРЫ
                relevance_score = matches_query(title, query)  # Только для информации
                
                # Убеждаемся, что relevance_score всегда число
                if relevance_score is None:
                    relevance_score = 0
                else:
                    relevance_score = float(relevance_score)

                # Цена - улучшенный парсинг
                price = "Цена не указана"
                price_selectors = [
                    '.a-price .a-offscreen',
                    '.a-price-whole',
                    '.a-price .a-price-whole',
                    'span[data-a-color="price"]',
                    '.a-price-range',
                    'span.a-price',
                    'span.a-offscreen'
                ]

                for price_selector in price_selectors:
                    price_elem = product.select_one(price_selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and any(char.isdigit() for char in price_text):
                            price = price_text
                            break

                # Изображение
                image = ""
                img_selectors = [
                    'img[data-image-latency="s-product-image"]',
                    'img[src*="images/I"]',
                    'img[data-old-hires]',
                    'img[src*="amazon"]',
                    'img.s-image'
                    ]

                for img_selector in img_selectors:
                    img_elem = product.select_one(img_selector)
                    if img_elem:
                        image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-old-hires')
                        if image:
                                break

                # Ссылка на товар - УЛУЧШЕННАЯ ЛОГИКА
                link = ""
                link_selectors = [
                    'h2 a[href*="/dp/"]',
                    'h2 a[href*="/gp/product/"]',
                    'a[href*="/dp/"]',
                    'a[href*="/gp/product/"]',
                    'a[data-cy="title-recipe-link"]',
                    'h2 a',
                    'a[data-asin]',
                    'a[href*="amazon.de/dp/"]',
                    'a[href*="amazon.de/gp/product/"]'
                ]

                for link_selector in link_selectors:
                    link_elem = product.select_one(link_selector)
                    if link_elem:
                        link = link_elem.get('href')
                        if link:
                            # Очищаем ссылку от лишних параметров
                            if '/dp/' in link:
                                # Извлекаем ASIN из ссылки
                                asin_start = link.find('/dp/') + 4
                                asin_end = link.find('/', asin_start)
                                if asin_end == -1:
                                    asin_end = link.find('?', asin_start)
                                if asin_end == -1:
                                    asin_end = len(link)
                                
                                asin = link[asin_start:asin_end]
                                if len(asin) >= 10:  # ASIN обычно 10 символов
                                    link = f"https://www.amazon.de/dp/{asin}"
                                    break
                            elif '/gp/product/' in link:
                                # Извлекаем product ID
                                product_start = link.find('/gp/product/') + 12
                                product_end = link.find('/', product_start)
                                if product_end == -1:
                                    product_end = link.find('?', product_start)
                                if product_end == -1:
                                    product_end = len(link)
                                
                                product_id = link[product_start:product_end]
                                if len(product_id) >= 10:
                                    link = f"https://www.amazon.de/gp/product/{product_id}"
                                    break
                            else:
                                # Если ссылка не содержит /dp/ или /gp/product/, но содержит amazon.de
                                if 'amazon.de' in link:
                                    if not link.startswith('http'):
                                        link = f"https://www.amazon.de{link}"
                                    break

                # Если ссылка все еще не найдена, попробуем найти ASIN в data-asin атрибуте
                if not link:
                    asin = product.get('data-asin')
                    if asin and len(asin) >= 10:
                        link = f"https://www.amazon.de/dp/{asin}"
                        logger.debug(f"🔗 Создана ссылка из ASIN: {link}")

                # Если ссылка все еще пустая, попробуем найти любую ссылку в товаре
                if not link:
                    all_links = product.find_all('a', href=True)
                    for a_tag in all_links:
                        href = a_tag.get('href', '')
                        if '/dp/' in href or '/gp/product/' in href:
                            if not href.startswith('http'):
                                href = f"https://www.amazon.de{href}"
                            link = href
                            break

                # Создаем результат - ВСЕ ТОВАРЫ БЕЗ ФИЛЬТРА
                result = {
                    'name': title,
                    'price': price,
                    'image': image,
                    'url': link,
                    'relevance_score': relevance_score,
                    'source': 'Amazon'
                }

                # Добавляем ВСЕ товары без фильтрации по релевантности
                results.append(result)
                logger.info(f"✅ Добавлен товар: {title[:50]}... (score: {relevance_score})")

                # Логируем информацию о ссылке для отладки
                if not link or link.strip() == '':
                    logger.warning(f"⚠️ Товар без ссылки: {title[:50]}...")
                else:
                    logger.debug(f"🔗 Ссылка найдена: {link[:50]}...")

            except Exception as e:
                logger.error(f"Error processing product {i}: {e}")
                continue
    
        logger.info(f"🎯 Найдено {len(results)} товаров на Amazon (ВСЕ НАЙДЕННЫЕ)")
        return results

    except Exception as e:
        logger.error(f"Error searching Amazon: {e}")
    return results
