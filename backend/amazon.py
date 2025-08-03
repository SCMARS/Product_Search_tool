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

    """
    if not product_name or not query:
        return False

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

    # Строгая проверка: если товар содержит слова аксессуаров, то он НЕ является смартфоном
    accessory_strict_keywords = ['hülle', 'case', 'cover', 'schutz', 'protection', 'folie', 'screen protector', 
                               'panzerglas', 'powerbank', 'charger', 'ladegerät', 'kabel', 'cable', 'adapter',
                               'stück', 'pack', 'set', 'kit', 'zubehör', 'accessory', 'protector', 'guard',
                               'displayschutz', 'kamera', 'camera', 'schutzglas', 'protection glass']
    if any(keyword in product_lower for keyword in accessory_strict_keywords):
        # Если товар содержит слова аксессуаров, то он НЕ является смартфоном
        return 0  # Полностью исключаем из результатов

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

    # Специальные названия для популярных товаров
    special_names = {
        'apple mouse': ['magic mouse', 'apple magic mouse'],
        'apple keyboard': ['magic keyboard', 'apple magic keyboard'],
        'apple watch': ['apple watch', 'iwatch'],
        'airpods': ['airpods', 'air pods'],
        'iphone': ['iphone'],
        'macbook': ['macbook'],
        'ipad': ['ipad'],
        'silicone caulking tools': ['silicone seam tool', 'caulking tool', 'silicone tool', 'seam tool'],
        'caulking tools': ['caulking tool', 'seam tool', 'silicone tool'],
        'silicone tools': ['silicone tool', 'caulking tool', 'seam tool'],
        'electric mosquito swatter': ['elektrische fliegenklatsche', 'electric fly swatter', 'mosquito killer'],
        'mosquito swatter': ['fliegenklatsche', 'fly swatter', 'mosquito killer'],
        'electric fly swatter': ['elektrische fliegenklatsche', 'electric mosquito swatter', 'fly killer']
    }

    # Проверяем специальные названия
    for search_term, alternatives in special_names.items():
        if search_term in query_lower:
            for alt_name in alternatives:
                if alt_name in product_lower:
                    score += 50  # Бонус за альтернативное название

    # Бонус за правильный порядок слов
    # Проверяем, идут ли слова в том же порядке что и в запросе
    last_position = -1
    ordered_words = 0
    for word in query_words:
        if len(word) > 2:  # Игнорируем короткие слова
            position = product_lower.find(word)
            if position > last_position:
                ordered_words += 1
                last_position = position

    # Бонус за правильный порядок
    if len(query_words) > 1:
        order_bonus = (ordered_words / len(query_words)) * 30
        score += int(order_bonus)

    # Штраф за слишком длинные названия (могут быть спам)
    if len(product_name) > 200:
        score -= 20


    if len(product_name) < 10:
        score -= 20

    # Бонус за наличие ключевых слов в правильных местах
    key_positions = ['tool', 'kit', 'set', 'professional', 'premium', 'electric', 'electronic']
    for key_word in key_positions:
        if key_word in product_lower:
            score += 8

    # Штраф за нерелевантные слова
    irrelevant_words = ['case', 'cover', 'protector', 'screen', 'film', 'adapter', 'cable', 'charger']
    for word in irrelevant_words:
        if word in product_lower and word not in query_lower:
            score -= 5

    # Финальная проверка минимального score
    if score >= min_score:
        logger.debug(f"✅ Товар прошел фильтр: '{product_name[:50]}...' (score: {score})")
        return score
    else:
        logger.debug(f"❌ Товар не прошел фильтр: '{product_name[:50]}...' (score: {score})")
        return 0

def search_amazon(query, limit=10, max_pages=1):
    """
    Поиск товаров на Amazon.de - ТОЛЬКО РЕАЛЬНЫЕ РЕЗУЛЬТАТЫ
    """
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # ТОЛЬКО ПЕРВАЯ СТРАНИЦА
        page = 1
        logger.info(f"Searching page {page}...")

        # Формируем URL для поиска с улучшенными параметрами
        search_params = {
            'k': query,
            'ref': 'sr_pg_1',
            'sprefix': query.replace(' ', '+'),  # Помогает с автодополнением
            'crid': '1234567890'  # Случайный ID для сессии
        }

        url = f"https://www.amazon.de/s?{urlencode(search_params)}"
        logger.info(f"🔍 Amazon URL: {url}")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')



        # Ищем товары на странице
        products = soup.find_all('div', {'data-component-type': 's-search-result'})

        logger.info(f"Found {len(products)} products on page {page}")

        logger.info(f"🔍 Обрабатываем {len(products)} товаров...")

        for i, product in enumerate(products):
            if len(results) >= limit:
                break

            logger.debug(f"🔍 Товар {i+1}/{len(products)}")

            try:
                # Название товара - пробуем разные селекторы
                title = None
                title_selectors = [
                    'h2 a span',  # Основной селектор
                    'h2 span',    # Альтернативный
                    'h2 a',       # Ссылка в заголовке
                    'h2',         # Сам заголовок
                    '.a-size-medium',  # Класс размера
                    '.a-size-mini'     # Маленький размер
                ]

                for selector in title_selectors:
                    title_elem = product.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 10:  # Минимальная длина названия
                            break

                if not title:
                    logger.debug("❌ Не найдено название товара")
                    continue

                logger.debug(f"📦 Найден товар: {title[:60]}...")

                # Проверяем релевантность и получаем score
                relevance_score = matches_query(title, query)
                if relevance_score < 100:  # Минимальный score для включения в результаты
                    continue

                logger.info(f"✅ Товар прошел фильтр: {title[:50]}...")

                # Цена - улучшенный парсинг с полной ценой
                price = "Цена не указана"

                # Сначала пробуем найти полную цену в блоке .a-price
                price_container = product.select_one('.a-price')
                if price_container:
                    # Ищем скрытый текст с полной ценой
                    offscreen = price_container.select_one('.a-offscreen')
                    if offscreen:
                        price_text = offscreen.get_text(strip=True)
                        if price_text and any(char.isdigit() for char in price_text):
                            price = price_text
                            logger.debug(f"💰 Найдена полная цена: {price}")
                    else:
                        # Если нет скрытого текста, собираем цену из частей
                        whole_part = price_container.select_one('.a-price-whole')
                        fraction_part = price_container.select_one('.a-price-fraction')
                        symbol_part = price_container.select_one('.a-price-symbol')

                        if whole_part:
                            whole_text = whole_part.get_text(strip=True)
                            symbol_text = symbol_part.get_text(strip=True) if symbol_part else ""
                            fraction_text = fraction_part.get_text(strip=True) if fraction_part else ""

                            # Собираем полную цену
                            if fraction_text:
                                price = f"{symbol_text}{whole_text},{fraction_text}"
                            else:
                                price = f"{symbol_text}{whole_text}"
                            logger.debug(f"💰 Собрана цена из частей: {price}")

                # Если цена все еще не найдена, пробуем другие селекторы
                if price == "Цена не указана":
                    price_selectors = [
                        '.a-price .a-offscreen',  # Цена внутри блока цены
                        '.a-price-range',  # Диапазон цен
                        '.a-text-price',   # Текстовая цена
                        '.a-color-price',   # Цветная цена
                        'span[class*="price"]'  # Любой span с price в классе
                    ]

                    for selector in price_selectors:
                        price_elem = product.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            if price_text and any(char.isdigit() for char in price_text):
                                price = price_text
                                logger.debug(f"💰 Найдена цена через селектор '{selector}': {price}")
                                break

                # Если цена все еще не найдена, пробуем найти любой текст с символами валют
                if price == "Цена не указана":
                    price_patterns = product.find_all(text=lambda text: text and ('€' in text or '$' in text or '£' in text) and any(c.isdigit() for c in text))
                    if price_patterns:
                        price = price_patterns[0].strip()
                        logger.debug(f"💰 Найдена цена через паттерн: {price}")

                # Ссылка - пробуем разные селекторы
                link = ""
                link_selectors = [
                    'h2 a',  # Основной селектор
                    'a[data-component-type="s-product-image"]',  # Ссылка на изображение
                    'a.a-link-normal',  # Обычная ссылка
                    '.s-link-style a',  # Ссылка в стиле поиска
                    'a[href*="/dp/"]',  # Прямая ссылка на товар
                    'a[href*="/gp/product/"]'  # Альтернативная ссылка на товар
                ]

                for selector in link_selectors:
                    link_elem = product.select_one(selector)
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        if href.startswith('/'):
                            link = f"https://www.amazon.de{href}"
                        else:
                            link = href
                        logger.debug(f"🔗 Найдена ссылка через селектор '{selector}': {link[:50]}...")
                        break

                if not link:
                    logger.warning(f"⚠️ Не найдена ссылка для товара: {title[:30]}...")

                # Изображение
                image = ""
                img_elem = product.select_one('img.s-image')
                if img_elem and img_elem.get('src'):
                    image = img_elem['src']

                # Описание - извлекаем реальное описание товара
                description = "Найдено на Amazon.de"

                # Пробуем найти описание товара
                desc_selectors = [
                    '.a-size-base-plus',  # Основное описание
                    '.a-size-base',       # Альтернативное описание
                    '.s-size-mini',       # Краткое описание
                    '[data-cy="title-recipe-review-snippet"]',  # Отзывы
                    '.a-row .a-size-small'  # Дополнительная информация
                ]

                for desc_selector in desc_selectors:
                    desc_elem = product.select_one(desc_selector)
                    if desc_elem:
                        desc_text = desc_elem.get_text(strip=True)
                        if desc_text and len(desc_text) > 20 and desc_text != title:
                            description = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text
                            break

                # Если описания нет, создаем из названия
                if description == "Найдено на Amazon.de":
                    # Извлекаем ключевые характеристики из названия
                    key_features = []
                    if 'bluetooth' in title.lower():
                        key_features.append('Bluetooth')
                    if 'wireless' in title.lower() or 'kabellos' in title.lower():
                        key_features.append('Беспроводной')
                    if 'rechargeable' in title.lower() or 'wiederaufladbar' in title.lower():
                        key_features.append('Перезаряжаемый')
                    if 'waterproof' in title.lower() or 'wasserdicht' in title.lower():
                        key_features.append('Водонепроницаемый')
                    if any(word in title.lower() for word in ['gb', 'tb', 'mb']):
                        storage_match = next((word for word in title.split() if any(unit in word.lower() for unit in ['gb', 'tb', 'mb'])), None)
                        if storage_match:
                            key_features.append(f'Память: {storage_match}')

                    if key_features:
                        description = f"Характеристики: {', '.join(key_features)}. Найдено на Amazon.de"
                    else:
                        description = f"Товар от Amazon.de. Цена: {price}"

                product_data = {
                    'name': title,
                    'price': price,
                    'url': link,
                    'image': image,
                    'description': description,
                    'relevance_score': relevance_score  # Добавляем score для сортировки
                }

                results.append(product_data)
                logger.info(f"✅ Добавлен товар: {title[:40]}... | Цена: {price}")

            except Exception as e:
                logger.error(f"❌ Ошибка обработки товара: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Ошибка поиска Amazon: {e}")
    
    # Сортируем результаты по релевантности (если есть поле relevance_score)
    if results:
        try:
            # Сортируем по убыванию релевантности
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            logger.info(f"✅ Amazon результаты отсортированы по релевантности")
        except Exception as e:
            logger.debug(f"Не удалось отсортировать результаты: {e}")

    # НЕТ ТЕСТОВЫХ ДАННЫХ - возвращаем только реальные результаты
    if not results:
        logger.info("❌ Amazon поиск не дал результатов")

    return results
