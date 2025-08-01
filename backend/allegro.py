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
            'защита': ['protector', 'protection'],
            
            # Инструменты
            'silicone caulking tools': ['silicone seam tool', 'caulking tool', 'silicone tool', 'seam tool'],
            'caulking tools': ['caulking tool', 'seam tool', 'silicone tool'],
            'silicone tools': ['silicone tool', 'caulking tool', 'seam tool'],
            'electric mosquito swatter': ['elektrische fliegenklatsche', 'electric fly swatter', 'mosquito killer'],
            'mosquito swatter': ['fliegenklatsche', 'fly swatter', 'mosquito killer'],
            'electric fly swatter': ['elektrische fliegenklatsche', 'electric mosquito swatter', 'fly killer']
        }

        query_lower = query.lower()
        title_lower = title.lower()

        # Проверяем транслитерацию - НЕ возвращаем сразу, а добавляем к общему score
        transliteration_bonus = 0
        for ru_word, en_variants in transliteration_map.items():
            if ru_word in query_lower:
                for en_variant in en_variants:
                    if en_variant in title_lower:
                        transliteration_bonus += 50  # Бонус за транслитерацию
                        break

        # Базовый алгоритм релевантности
        score = 0
        
        # Точное совпадение всей фразы
        if query_lower in title_lower:
            score += 150
        
        # Разбиваем на слова
        query_words = query_lower.split()
        title_words = title_lower.split()
        
        # Подсчитываем совпадающие слова
        matched_words = 0
        for q_word in query_words:
            if len(q_word) > 2:  # Игнорируем короткие слова
                for t_word in title_words:
                    if q_word in t_word or t_word in q_word:
                        matched_words += 1
                        break
        
        # Бонус за совпадающие слова
        if len(query_words) > 0:
            match_percentage = matched_words / len(query_words)
            score += int(match_percentage * 60)
        
        # Бонус за порядок слов
        last_pos = -1
        ordered_count = 0
        for q_word in query_words:
            if len(q_word) > 2:
                pos = title_lower.find(q_word)
                if pos > last_pos:
                    ordered_count += 1
                    last_pos = pos
        
        if len(query_words) > 1:
            order_bonus = (ordered_count / len(query_words)) * 40
            score += int(order_bonus)
        
        # Бонус за ключевые слова
        key_words = ['tool', 'kit', 'set', 'professional', 'premium', 'electric', 'electronic']
        for key_word in key_words:
            if key_word in title_lower:
                score += 10
        
        # Штраф за нерелевантные слова
        irrelevant_words = ['case', 'cover', 'protector', 'screen', 'film', 'adapter', 'cable', 'charger']
        for word in irrelevant_words:
            if word in title_lower and word not in query_lower:
                score -= 20
        
        # Штраф за слишком длинные названия
        if len(title) > 200:
            score -= 25
        
        # Штраф за слишком короткие названия
        if len(title) < 10:
            score -= 30
        
        # Добавляем бонус за транслитерацию
        score += transliteration_bonus
        
        return score

    def translate_query(self, query: str) -> str:
        """Простой перевод русских запросов на польский/английский"""
        translations = {
            'телефон': 'telefon', 'смартфон': 'smartfon', 'айфон': 'iphone',
            'самсунг': 'samsung', 'ноутбук': 'laptop', 'компьютер': 'komputer',
            'планшет': 'tablet', 'наушники': 'słuchawki', 'колонки': 'głośniki',
            'кофемашина': 'ekspres do kawy', 'пылесос': 'odkurzacz',
            'холодильник': 'lodówka', 'стиральная машина': 'pralka',
            'кроссовки': 'buty sportowe', 'куртка': 'kurtka', 'джинсы': 'jeansy',
            'мебель': 'meble', 'стол': 'stół', 'стул': 'krzesło', 'диван': 'sofa'
        }

        query_lower = query.lower()
        for ru_word, pl_word in translations.items():
            if ru_word in query_lower:
                query_lower = query_lower.replace(ru_word, pl_word)

        return query_lower

    def get_proxy_config(self):
        """Получение конфигурации прокси с ротацией"""
        import os
        import random

        # Проверяем переменные окружения для прокси
        proxy_server = os.getenv('PROXY_SERVER')
        proxy_username = os.getenv('PROXY_USERNAME')
        proxy_password = os.getenv('PROXY_PASSWORD')

        if proxy_server:
            proxy_config = {
                'server': proxy_server
            }

            if proxy_username and proxy_password:
                proxy_config['username'] = proxy_username
                proxy_config['password'] = proxy_password

            logger.info(f"🌐 Используем настроенный прокси: {proxy_server}")
            return proxy_config

        # Загружаем список прокси из файла
        try:
            proxy_file_path = os.path.join(os.path.dirname(__file__), 'proxy_list.txt')
            with open(proxy_file_path, 'r') as f:
                proxy_list = [line.strip() for line in f.readlines() if line.strip()]

            if proxy_list:
                # Выбираем случайный прокси
                selected_proxy_ip = random.choice(proxy_list)
                selected_proxy = f"http://{selected_proxy_ip}"

                logger.info(f"🌐 Выбран случайный прокси: {selected_proxy}")
                return {'server': selected_proxy}

        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить список прокси: {e}")

        logger.info("🌐 Прокси не настроен, используем прямое подключение")
        return None

    def change_ip_address(self):
        """Попытка смены IP адреса"""
        try:
            import subprocess
            import os

            # Метод 1: Перезапуск сетевого интерфейса (требует sudo)
            vpn_command = os.getenv('VPN_RECONNECT_COMMAND')
            if vpn_command:
                logger.info("🔄 Пытаемся сменить IP через VPN...")
                subprocess.run(vpn_command.split(), timeout=30)
                import time
                time.sleep(10)  # Ждем подключения
                return True

            # Метод 2: Команда для смены IP (зависит от провайдера)
            ip_change_command = os.getenv('IP_CHANGE_COMMAND')
            if ip_change_command:
                logger.info("🔄 Пытаемся сменить IP...")
                subprocess.run(ip_change_command.split(), timeout=30)
                import time
                time.sleep(5)
                return True

        except Exception as e:
            logger.error(f"❌ Не удалось сменить IP: {e}")

        return False

    def get_current_ip(self):
        """Получение текущего IP адреса"""
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                ip_data = response.json()
                return ip_data.get('origin', 'Unknown')
        except Exception as e:
            logger.debug(f"Не удалось получить IP: {e}")

        return "Unknown"

    def test_proxy(self, proxy_config):
        """Тестирование работоспособности прокси"""
        if not proxy_config:
            return True

        try:
            import requests
            proxies = {
                'http': proxy_config['server'],
                'https': proxy_config['server']
            }

            # Тестируем прокси на простом сайте
            response = requests.get('http://httpbin.org/ip',
                                  proxies=proxies,
                                  timeout=10)

            if response.status_code == 200:
                ip_data = response.json()
                logger.info(f"✅ Прокси работает, IP: {ip_data.get('origin', 'Unknown')}")
                return True
            else:
                logger.warning(f"⚠️ Прокси вернул статус: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"❌ Прокси не работает: {e}")
            return False

    def get_working_proxy(self, max_attempts=5):
        """Получение рабочего прокси с несколькими попытками"""
        for attempt in range(max_attempts):
            proxy_config = self.get_proxy_config()

            if not proxy_config:
                return None

            if self.test_proxy(proxy_config):
                return proxy_config

            logger.info(f"🔄 Попытка {attempt + 1}/{max_attempts}: пробуем другой прокси...")

        logger.warning("❌ Не удалось найти рабочий прокси, используем прямое подключение")
        return None

    async def detect_captcha(self, page):
        """Обнаружение капчи на странице"""
        try:
            # Ищем различные элементы капчи
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'div[class*="captcha"]',
                'img[src*="captcha"]',
                '[data-testid*="captcha"]',
                'form[action*="captcha"]',
                '.g-recaptcha',
                '#captcha',
                'text="Przepisz kod z obrazka"',
                'text="Aplikacja przekroczyła limit"'
            ]

            for selector in captcha_selectors:
                element = page.locator(selector).first
                if await element.count() > 0:
                    logger.warning(f"🤖 Обнаружена капча: {selector}")
                    return True

            # Проверяем текст страницы на наличие ключевых слов
            page_content = await page.content()
            captcha_keywords = [
                'captcha',
                'Przepisz kod z obrazka',
                'Aplikacja przekroczyła limit zapytań',
                'przekroczyła limit',
                'Kod błędu',
                'POTWIERDŹ',
                'ffb8115a-3756-4f23-a833-80d38e2',  # Конкретный код ошибки
                'Captcha',
                'limit zapytań'
            ]

            for keyword in captcha_keywords:
                if keyword.lower() in page_content.lower():
                    logger.warning(f"🤖 Обнаружена капча по ключевому слову: {keyword}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Ошибка обнаружения капчи: {e}")
            return False

    async def solve_captcha_2captcha(self, page):
        """Решение капчи через 2captcha сервис"""
        try:
            import os
            api_key = os.getenv('CAPTCHA_API_KEY')

            if not api_key:
                logger.error("❌ API ключ 2captcha не найден в переменных окружения")
                logger.info("💡 Добавьте CAPTCHA_API_KEY в файл .env")
                return False

            logger.info(f"🔑 Используем 2captcha API ключ: {api_key[:10]}...")

            # Делаем скриншот страницы с капчей
            screenshot_path = 'captcha_screenshot.png'
            await page.screenshot(path=screenshot_path, full_page=True)

            # Отправляем в 2captcha
            from twocaptcha import TwoCaptcha
            solver = TwoCaptcha(api_key)

            logger.info("🤖 Отправляем капчу в 2captcha...")

            try:
                result = solver.normal(screenshot_path)
                captcha_text = result['code']
                logger.info(f"✅ Капча решена: {captcha_text}")

                # Ищем поле ввода капчи и вводим результат
                input_selectors = [
                    'input[name*="captcha"]',
                    'input[id*="captcha"]',
                    'input[type="text"]',
                    'input[placeholder*="kod"]'
                ]

                for selector in input_selectors:
                    input_element = page.locator(selector).first
                    if await input_element.count() > 0:
                        await input_element.fill(captcha_text)
                        logger.info(f"✅ Введен код капчи в поле: {selector}")
                        break

                # Ищем кнопку подтверждения
                submit_selectors = [
                    'button:has-text("POTWIERDŹ")',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Confirm")',
                    'button:has-text("Submit")'
                ]

                for selector in submit_selectors:
                    submit_button = page.locator(selector).first
                    if await submit_button.count() > 0:
                        await submit_button.click()
                        logger.info(f"✅ Нажата кнопка подтверждения: {selector}")
                        break

                # Ждем загрузки после решения капчи
                await page.wait_for_load_state("networkidle", timeout=10000)

                # Проверяем, исчезла ли капча
                if not await self.detect_captcha(page):
                    logger.info("✅ Капча успешно решена!")
                    return True
                else:
                    logger.warning("⚠️ Капча все еще присутствует")
                    return False

            except Exception as e:
                logger.error(f"❌ Ошибка решения капчи через 2captcha: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка в solve_captcha_2captcha: {e}")
            return False

    def search_products_simple(self, query: str) -> List[Dict[str, Any]]:
        """
        Улучшенный простой поиск через HTTP запросы
        """
        products = []

        try:
            import time
            import random
            import urllib.parse

            # Переводим запрос
            translated_query = self.translate_query(query)
            encoded_query = urllib.parse.quote_plus(translated_query)
            search_url = f"https://allegro.pl/listing?string={encoded_query}"

            logger.info(f"🔍 HTTP поиск: {query} → {translated_query}")

            # Улучшенные заголовки с ротацией
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]

            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }

            # Случайная задержка
            time.sleep(random.uniform(0.5, 2.0))

            session = requests.Session()
            session.headers.update(headers)

            response = session.get(search_url, timeout=15)

            if response.status_code == 403:
                logger.warning("403 ошибка, пробуем альтернативный URL")
                # Пробуем другой формат URL
                alt_url = f"https://allegro.pl/kategoria/elektronika?string={encoded_query}"
                response = session.get(alt_url, timeout=15)

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
                    headless=True,  # Возвращаем headless режим
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
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

                # ПАУЗА ДЛЯ ПРОСМОТРА СТРАНИЦЫ
                logger.info("🔍 БРАУЗЕР ОТКРЫТ! Посмотрите что происходит на странице...")

                # Проверяем наличие капчи
                captcha_detected = await self.detect_captcha(page)
                if captcha_detected:
                    logger.warning("🤖 Обнаружена капча! Пытаемся решить...")
                    captcha_solved = await self.solve_captcha_2captcha(page)
                    if captcha_solved:
                        logger.info("✅ Капча решена, продолжаем поиск...")
                        await asyncio.sleep(3)
                    else:
                        logger.error("❌ Не удалось решить капчу автоматически")
                        logger.info("⏳ Ожидание ручного решения капчи (30 секунд)...")
                        await asyncio.sleep(30)

                        # Проверяем еще раз после ожидания
                        if await self.detect_captcha(page):
                            logger.error("❌ Капча все еще присутствует, прерываем поиск")
                            return []
                        else:
                            logger.info("✅ Капча решена вручную, продолжаем")

                await asyncio.sleep(15)  # 15 секунд для просмотра

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
                                        # Основные селекторы с валютой
                                        'span:has-text("zł")',
                                        'div:has-text("zł")',
                                        '*:has-text("zł")',

                                        # Data-testid селекторы
                                        '[data-testid*="price"]',
                                        '[data-testid*="Price"]',
                                        '[data-testid="price-container"]',
                                        '[data-testid="price"]',
                                        '[data-testid="price-label"]',
                                        '[data-testid="price-value"]',

                                        # Классы цен
                                        'span[class*="price"]',
                                        'div[class*="price"]',
                                        '[class*="_price"]',
                                        '[class*="amount"]',
                                        '[class*="cost"]',
                                        '.price',

                                        # Data-role селекторы
                                        'span[data-role="price"]',
                                        '[data-role="price"]',

                                        # Дополнительные
                                        'span:has-text("PLN")',
                                        'span:has-text(",")',
                                        '[aria-label*="price"]',
                                        '[aria-label*="cena"]',
                                        '.offer-price',
                                        '.product-price'
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

                                    # Извлекаем изображение - улучшенный метод
                                    image = ""
                                    image_selectors = [
                                        'img[src*="allegro"]',
                                        'img[data-src*="allegro"]',
                                        'img[src]',
                                        'img[data-src]',
                                        'img[data-lazy-src]'
                                    ]

                                    for img_selector in image_selectors:
                                        img_element = element.locator(img_selector).first
                                        if await img_element.count() > 0:
                                            src = await img_element.get_attribute('src') or await img_element.get_attribute('data-src') or await img_element.get_attribute('data-lazy-src')
                                            if src:
                                                # Формируем полную ссылку
                                                if src.startswith('//'):
                                                    image = f"https:{src}"
                                                elif src.startswith('/'):
                                                    image = f"https://allegro.pl{src}"
                                                else:
                                                    image = src

                                                # Проверяем что это не иконка
                                                if not any(x in image.lower() for x in ['icon', 'logo', 'sprite']) or 'product' in image.lower():
                                                    break

                                    if not image:
                                        # Fallback - любое изображение
                                        img_element = element.locator('img').first
                                        if await img_element.count() > 0:
                                            src = await img_element.get_attribute('src')
                                            if src:
                                                image = src if src.startswith('http') else f"https://allegro.pl{src}"

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

    def search_mobile_version(self, query: str) -> List[Dict[str, Any]]:
        """Поиск через мобильную версию Allegro"""
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            mobile_url = f"https://m.allegro.pl/listing?string={encoded_query}"

            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pl-PL,pl;q=0.9'
            }

            response = requests.get(mobile_url, headers=mobile_headers, timeout=10)

            if response.status_code == 200:
                return self.parse_simple_html(response.text, query)

        except Exception as e:
            logger.error(f"Ошибка мобильной версии: {e}")

        return []

    def search_by_categories(self, query: str) -> List[Dict[str, Any]]:
        """Поиск через основные категории"""
        categories = {
            'elektronika': ['телефон', 'смартфон', 'айфон', 'ноутбук', 'компьютер', 'планшет'],
            'dom-i-ogrod': ['кофемашина', 'пылесос', 'холодильник', 'мебель'],
            'moda': ['кроссовки', 'куртка', 'джинсы', 'футболка'],
            'sport-i-turystyka': ['велосипед', 'лыжи', 'фитнес']
        }

        query_lower = query.lower()
        selected_category = 'elektronika'  # По умолчанию

        # Определяем категорию по ключевым словам
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                selected_category = category
                break

        try:
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            category_url = f"https://allegro.pl/kategoria/{selected_category}?string={encoded_query}"

            response = requests.get(category_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return self.parse_simple_html(response.text, query)

        except Exception as e:
            logger.error(f"Ошибка поиска по категориям: {e}")

        return []

    def parse_simple_html(self, html: str, query: str) -> List[Dict[str, Any]]:
        """Простой парсинг HTML с базовым извлечением цен и изображений"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            products = []

            # Ищем ссылки на товары (простой метод, который работал)
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')
                if '/oferta/' in href:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:
                        score = self.calculate_relevance_score(title, query)
                        if score >= 30:
                            # Ищем цену рядом с товаром - улучшенный поиск
                            price = "Цена не указана"
                            parent = link.find_parent()

                            # Расширяем поиск на несколько уровней вверх
                            search_containers = [parent]
                            if parent:
                                # Добавляем родительские элементы
                                grandparent = parent.find_parent()
                                if grandparent:
                                    search_containers.append(grandparent)
                                    great_grandparent = grandparent.find_parent()
                                    if great_grandparent:
                                        search_containers.append(great_grandparent)

                            for container in search_containers:
                                if not container:
                                    continue

                                # Сначала ищем по селекторам
                                price_selectors = [
                                    '[data-testid*="price"]',
                                    '[class*="price"]',
                                    '[class*="amount"]',
                                    '[class*="cost"]',
                                    '.price'
                                ]

                                for selector in price_selectors:
                                    price_elem = container.select_one(selector)
                                    if price_elem:
                                        price_text = price_elem.get_text(strip=True)
                                        if price_text and 'zł' in price_text:
                                            price = price_text
                                            break

                                if price != "Цена не указана":
                                    break

                                # Если не нашли по селекторам, ищем регулярными выражениями
                                price_text = container.get_text()
                                import re

                                # Улучшенные паттерны для поиска цен
                                price_patterns = [
                                    r'\d+[,\s]*\d*\s*zł',  # 123 zł или 123,45 zł
                                    r'\d+[,\.]\d{2}\s*zł',  # 123.45 zł или 123,45 zł
                                    r'\d+\s*zł',           # 123zł
                                    r'\d+[,\s]*\d*\s*PLN', # 123 PLN
                                ]

                                for pattern in price_patterns:
                                    price_match = re.search(pattern, price_text)
                                    if price_match:
                                        price = price_match.group().strip()
                                        break

                                if price != "Цена не указана":
                                    break

                            # Ищем изображение - улучшенный поиск
                            image = ""

                            # Ищем в тех же контейнерах что и цену
                            for container in search_containers:
                                if not container:
                                    continue

                                # Расширенные селекторы для изображений
                                img_selectors = [
                                    'img[src*="allegro"]',
                                    'img[data-src*="allegro"]',
                                    'img[data-lazy-src*="allegro"]',
                                    'img[src*="product"]',
                                    'img[data-src*="product"]',
                                    'img[src]',
                                    'img[data-src]',
                                    'img[data-lazy-src]'
                                ]

                                for selector in img_selectors:
                                    img_elem = container.select_one(selector)
                                    if img_elem:
                                        src = (img_elem.get('src') or
                                              img_elem.get('data-src') or
                                              img_elem.get('data-lazy-src') or
                                              img_elem.get('data-original'))

                                        if src:
                                            # Формируем полную ссылку
                                            if src.startswith('//'):
                                                image = f"https:{src}"
                                            elif src.startswith('/'):
                                                image = f"https://allegro.pl{src}"
                                            else:
                                                image = src

                                            # Проверяем что это не иконка или логотип
                                            if not any(x in image.lower() for x in ['icon', 'logo', 'sprite', 'placeholder']) or 'product' in image.lower():
                                                break

                                if image:
                                    break

                            # Формируем полную ссылку
                            if not href.startswith('http'):
                                href = f"https://allegro.pl{href}"

                            product = {
                                'name': title,
                                'price': price,
                                'url': href,
                                'image': image,
                                'description': title,
                                'relevance_score': score
                            }
                            products.append(product)

                            if len(products) >= 10:
                                break

            # Сортируем по релевантности
            if products:
                products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                logger.info(f"✅ Результаты отсортированы по релевантности")

            logger.info(f"✅ Найдено {len(products)} товаров через простой парсинг")
            return products

        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return []


# Синхронная обертка
def search_allegro_improved(query: str, max_pages: int = 1, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Основная функция для поиска на Allegro
    """
    try:
        # Создаем экземпляр скрапера
        scraper = AllegroScraper()

        # Проверяем текущий IP
        current_ip = scraper.get_current_ip()
        logger.info(f"🌐 Текущий IP: {current_ip}")

        # Сначала пробуем простой HTTP поиск с разными User-Agent
        logger.info(f"🔍 Попытка HTTP поиска на Allegro: {query}")
        
        # Пробуем разные User-Agent для обхода блокировок
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        
        for i, user_agent in enumerate(user_agents):
            try:
                logger.info(f"🔍 Попытка {i+1}/4 с User-Agent: {user_agent[:50]}...")
                scraper.headers['User-Agent'] = user_agent
                http_results = scraper.search_products_simple(query)
                
                if http_results and len(http_results) > 0:
                    logger.info(f"✅ HTTP поиск успешен с User-Agent {i+1}: найдено {len(http_results)} товаров")
                    return http_results
                    
            except Exception as e:
                logger.error(f"❌ Ошибка HTTP поиска с User-Agent {i+1}: {e}")
                continue

        logger.info("⚠️ HTTP поиск не дал результатов, пробуем альтернативные методы...")

        # Метод 2: Поиск через категории без CAPTCHA
        try:
            logger.info("🔍 Пробуем поиск по категориям...")
            category_results = scraper.search_by_categories(query)
            if category_results and len(category_results) > 0:
                logger.info(f"✅ Поиск по категориям: найдено {len(category_results)} товаров")
                return category_results
        except Exception as e:
            logger.error(f"❌ Ошибка поиска по категориям: {e}")

        # Метод 3: Мобильная версия
        try:
            logger.info("🔍 Пробуем мобильную версию...")
            mobile_results = scraper.search_mobile_version(query)
            if mobile_results and len(mobile_results) > 0:
                logger.info(f"✅ Мобильная версия: найдено {len(mobile_results)} товаров")
                return mobile_results
        except Exception as e:
            logger.error(f"❌ Ошибка мобильной версии: {e}")

        # Если ничего не сработало, возвращаем пустой список вместо fallback
        logger.warning("❌ Все методы поиска Allegro не сработали, возвращаем пустой список")
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
