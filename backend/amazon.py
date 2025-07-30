import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from urllib.parse import urlencode, quote_plus

logger = logging.getLogger(__name__)

def matches_query(product_name, query, min_score=30):
    """
    Проверяет, соответствует ли название товара поисковому запросу
    Улучшенная версия для точного поиска
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
        score += 100  # Максимальный бонус за точное совпадение
        logger.debug(f"🎯 ТОЧНОЕ СОВПАДЕНИЕ: '{query_lower}' в '{product_lower}'")

    # Проверяем каждое слово из запроса
    for word in query_words:
        if len(word) > 1 and word in product_lower:  # Учитываем даже короткие важные слова
            if len(word) <= 2:
                score += 5   # Маленький бонус за короткие слова (11, 16, pro)
            elif len(word) <= 4:
                score += 15  # Средний бонус за средние слова (ipad, pro)
            else:
                score += 20  # Большой бонус за длинные слова
            matched_words += 1

    # Бонус за процент совпавших слов
    if len(query_words) > 0:
        match_percentage = matched_words / len(query_words)
        score += int(match_percentage * 30)  # До 30 дополнительных баллов

    # ОГРОМНЫЙ бонус за точное совпадение бренда в начале названия
    if len(query_words) >= 1:
        brand = query_words[0]  # Первое слово как бренд
        if product_lower.startswith(brand.lower()) or f" {brand.lower()} " in product_lower:
            score += 50  # Большой бонус за правильный бренд

    # Проверяем фразы из 2 слов
    for i in range(len(query_words) - 1):
        phrase = f"{query_words[i]} {query_words[i+1]}"
        if len(phrase) > 3 and phrase in product_lower:  # Минимум 3 символа
            score += 25  # Бонус за фразу из 2 слов

    # Проверяем фразы из 3 слов
    for i in range(len(query_words) - 2):
        phrase = f"{query_words[i]} {query_words[i+1]} {query_words[i+2]}"
        if phrase in product_lower:
            score += 35  # Больший бонус за фразу из 3 слов

    # Проверяем фразы из 4+ слов
    for i in range(len(query_words) - 3):
        phrase = " ".join(query_words[i:i+4])
        if phrase in product_lower:
            score += 50  # Максимальный бонус за длинную фразу

    # Дополнительный бонус за точное совпадение всего запроса
    if query_lower in product_lower:
        score += 40

    # Специальные названия для популярных товаров
    special_names = {
        'apple mouse': ['magic mouse', 'apple magic mouse'],
        'apple keyboard': ['magic keyboard', 'apple magic keyboard'],
        'apple watch': ['apple watch', 'iwatch'],
        'airpods': ['airpods', 'air pods'],
        'iphone': ['iphone'],
        'macbook': ['macbook'],
        'ipad': ['ipad']
    }

    # Проверяем специальные названия
    for search_term, alternatives in special_names.items():
        if search_term in query_lower:
            for alt_name in alternatives:
                if alt_name in product_lower:
                    score += 35  # Бонус за альтернативное название

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

    if ordered_words >= 2:
        score += ordered_words * 5  # Бонус за каждое слово в правильном порядке

    # УНИВЕРСАЛЬНЫЙ бонус за основные товары (не аксессуары)
    # Ищем признаки основного товара для ЛЮБОГО бренда
    main_product_indicators = [
        'gb', 'ssd', 'ram', 'memory', 'speicher', 'inch', 'zoll', '"', 'mm', 'cm',
        'gps', 'cellular', 'wifi', 'bluetooth', 'processor', 'cpu', 'gpu',
        'battery', 'akku', 'mah', 'watt', 'volt', 'amp', 'hz', 'ghz'
    ]

    if any(indicator in product_lower for indicator in main_product_indicators):
        score += 30  # Бонус за основной товар (не аксессуар)
    
    # УНИВЕРСАЛЬНАЯ фильтрация аксессуаров для ВСЕХ товаров
    # Если ищем аксессуары - НЕ штрафуем их
    looking_for_accessories = any(word in query_lower for word in [
        'чехол', 'case', 'cover', 'hülle', 'schutz', 'защита', 'клавиатура', 'keyboard',
        'кабель', 'cable', 'adapter', 'адаптер', 'сумка', 'bag', 'tasche', 'charger',
        'ladegerät', 'ladekabel', 'armband', 'strap', 'band', 'ремешок'
    ])

    if not looking_for_accessories:
        # УНИВЕРСАЛЬНЫЙ список аксессуаров для ВСЕХ брендов
        accessory_keywords = [
            # Чехлы и защита
            'hülle', 'case', 'cover', 'tasche', 'bag', 'schutz', 'protection', 'folie', 'screen',
            # Кабели и адаптеры
            'kabel', 'cable', 'ladekabel', 'schnellladekabel', 'adapter', 'charger', 'ladegerät',
            'usb-c', 'usb c', 'lightning', 'magsafe', 'magnetisch', 'magnetic',
            # Подставки и держатели
            'ständer', 'stand', 'halter', 'holder', 'dock', 'station',
            # Клавиатуры и мыши
            'tastatur', 'keyboard', 'maus', 'mouse', 'tastenkappen', 'keycaps',
            # Ремешки и браслеты
            'armband', 'strap', 'band', 'bracelet', 'wristband',
            # Сетевые аксессуары
            'ethernet', 'lan', 'hub', 'network', 'netzwerk', 'rj45',
            # Заглушки и мелочи
            'staubschutz', 'stöpsel', 'stecker', 'dust', 'plug',
            # Замена и ремонт
            'ersatz', 'replacement', 'repair', 'reparatur', 'zubehör', 'accessory',
            # Языковые аксессуары
            'arabische', 'arabic', 'russian', 'deutsch', 'english'
        ]

        # Штрафуем аксессуары для ВСЕХ товаров одинаково
        accessory_count = 0
        for keyword in accessory_keywords:
            if keyword in product_lower:
                accessory_count += 1

        # Штраф зависит от количества "аксессуарных" слов
        if accessory_count >= 2:
            score -= 30  # Большой штраф если много аксессуарных слов
        elif accessory_count == 1:
            score -= 15  # Маленький штраф если одно слово (может быть совместимость)
    
    # Проверяем минимальный порог
    logger.info(f"🔍 Товар: {product_name[:60]}... | Score: {score} | Порог: {min_score}")

    # Специальная отладка для Apple товаров
    if 'apple' in query_lower and 'apple' in product_lower:
        logger.info(f"🍎 APPLE товар найден: {product_name[:40]}... | Score: {score}")

    if score >= min_score:
        logger.info(f"✅ ПРИНЯТ: {product_name[:50]}... (Score: {score})")
        return True
    else:
        logger.info(f"❌ ОТКЛОНЕН: {product_name[:50]}... (Score: {score})")
        return False

def search_amazon(query, limit=3, max_pages=1):
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

        # Сохраняем HTML для отладки Apple товаров
        if 'apple mouse' in query.lower():
            try:
                with open('backend/debug_amazon_apple_mouse.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info("💾 Сохранен HTML для отладки: debug_amazon_apple_mouse.html")
            except Exception as e:
                logger.debug(f"Не удалось сохранить HTML: {e}")

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

                # Проверяем релевантность
                if not matches_query(title, query):
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
                    'description': description
                }

                results.append(product_data)
                logger.info(f"✅ Добавлен товар: {title[:40]}... | Цена: {price}")

            except Exception as e:
                logger.error(f"❌ Ошибка обработки товара: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Ошибка поиска Amazon: {e}")
    
    # НЕТ ТЕСТОВЫХ ДАННЫХ - возвращаем только реальные результаты
    if not results:
        logger.info("❌ Amazon поиск не дал результатов")

    return results
