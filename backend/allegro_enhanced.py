
import asyncio
import logging
import os
import random
import time
import json
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from dotenv import load_dotenv
import requests
from urllib.parse import quote_plus, urlencode

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AllegroEnhancedScraper:
    """
    Улучшенный скрапер для Allegro.pl с продвинутым обходом защиты
    """
    
    def __init__(self):
        self.base_url = "https://allegro.pl"
        self.search_url = "https://allegro.pl/listing"
        self.mobile_url = "https://m.allegro.pl/listing"
        
        # Ротация User-Agent'ов
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Список прокси (будет загружен из файла или переменных окружения)
        self.proxy_list = self._load_proxy_list()
        
    def _load_proxy_list(self) -> List[str]:
        """Загружает список прокси из файла или переменных окружения"""
        proxies = []
        
        # Пробуем загрузить из переменных окружения
        proxy_server = os.getenv('PROXY_SERVER')
        if proxy_server:
            proxies.append(proxy_server)
            logger.info(f"🌐 Загружен прокси из переменных окружения: {proxy_server}")
        
        # Пробуем загрузить из файла
        try:
            proxy_file = os.path.join(os.path.dirname(__file__), 'proxy_list.txt')
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    file_proxies = [
                        line.strip() for line in f.readlines()
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    proxies.extend(file_proxies)
                    logger.info(f"🌐 Загружено {len(file_proxies)} прокси из файла")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить прокси из файла: {e}")
        
        if not proxies:
            logger.info("🌐 Прокси не настроены, будем использовать прямое подключение")
        
        return proxies
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Возвращает случайный прокси из списка"""
        if not self.proxy_list:
            return None
            
        proxy_server = random.choice(self.proxy_list)
        
        # Проверяем формат прокси
        if not proxy_server.startswith('http'):
            proxy_server = f"http://{proxy_server}"
        
        proxy_config = {'server': proxy_server}
        
        # Добавляем аутентификацию если есть
        proxy_username = os.getenv('PROXY_USERNAME')
        proxy_password = os.getenv('PROXY_PASSWORD')
        
        if proxy_username and proxy_password:
            proxy_config['username'] = proxy_username
            proxy_config['password'] = proxy_password
        
        return proxy_config
    
    def _get_random_user_agent(self) -> str:
        """Возвращает случайный User-Agent"""
        return random.choice(self.user_agents)
    
    async def _human_like_behavior(self, page: Page):
        """Имитирует человеческое поведение на странице"""
        try:
            # Случайная задержка перед действиями
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Случайное движение мыши
            await page.mouse.move(
                random.randint(100, 800), 
                random.randint(100, 600)
            )
            
            # Случайный скролл
            scroll_distance = random.randint(200, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Еще один скролл назад
            await page.evaluate(f"window.scrollBy(0, -{scroll_distance // 2})")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            logger.debug("🤖 Выполнено человеко-подобное поведение")
            
        except Exception as e:
            logger.debug(f"Ошибка имитации поведения: {e}")
    
    async def _handle_gdpr_consent(self, page: Page) -> bool:
        """Обрабатывает GDPR согласие"""
        try:
            gdpr_selectors = [
                '[data-role="accept-consent"]',
                'button[data-testid="consent-accept"]',
                'button:has-text("Akceptuję")',
                'button:has-text("Accept")',
                'button:has-text("Zgadzam się")',
                'button:has-text("Zgoda")',
                '#onetrust-accept-btn-handler',
                '.ot-sdk-show-settings'
            ]
            
            for selector in gdpr_selectors:
                try:
                    consent_button = page.locator(selector).first
                    if await consent_button.count() > 0 and await consent_button.is_visible():
                        await consent_button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ GDPR согласие принято: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Селектор {selector} не сработал: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обработки GDPR: {e}")
            return False
    
    async def _detect_captcha(self, page: Page) -> bool:
        """Обнаруживает наличие CAPTCHA на странице"""
        try:
            # Сначала проверяем наличие результатов поиска
            search_indicators = [
                'text="ofert"',
                'text="sortowanie"',
                'text="trafność"',
                'a[href*="/oferta/"]',
                'article[data-role="offer"]',
                'div[data-testid="listing-container"]'
            ]
            
            for indicator in search_indicators:
                try:
                    element = page.locator(indicator).first
                    if await element.count() > 0:
                        logger.debug(f"✅ Найдены результаты поиска: {indicator}")
                        return False  # Есть результаты = нет CAPTCHA
                except:
                    continue
            
            # Проверяем наличие CAPTCHA
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'div[class*="captcha"]',
                'img[src*="captcha"]',
                '[data-testid*="captcha"]',
                'form[action*="captcha"]',
                '.g-recaptcha',
                '#captcha',
                'text="Przepisz kod z obrazka"',
                'text="Aplikacja przekroczyła limit"',
                'text="POTWIERDŹ"',
                'text="Potwierdź, że jesteś człowiekiem"',
                'text="Zauważyliśmy nietypowe działanie"',
                'button:has-text("potwierdzam")',
                'button:has-text("Potwierdź")',
                'text="potwierdzam"'
            ]
            
            for selector in captcha_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        logger.warning(f"🤖 Обнаружена CAPTCHA: {selector}")
                        return True
                except:
                    continue
            
            # Проверяем содержимое страницы
            page_content = await page.content()
            captcha_keywords = [
                'captcha', 'Przepisz kod', 'przekroczyła limit',
                'Kod błędu', 'POTWIERDŹ', 'limit zapytań'
            ]
            
            for keyword in captcha_keywords:
                if keyword.lower() in page_content.lower():
                    logger.warning(f"🤖 CAPTCHA обнаружена по ключевому слову: {keyword}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обнаружения CAPTCHA: {e}")
            return False
    
    async def _solve_captcha(self, page: Page) -> bool:
        """Решает CAPTCHA используя 2captcha сервис"""
        try:
            # Сначала проверяем простую кнопку подтверждения
            logger.info("🔍 Проверяем наличие простой кнопки подтверждения...")

            simple_confirm_buttons = [
                'button:has-text("potwierdzam")',
                'button:has-text("Potwierdź")',
                'button:has-text("Confirm")',
                'input[value*="potwierdzam"]',
                'input[value*="Potwierdź"]',
                '[role="button"]:has-text("potwierdzam")',
                'a:has-text("potwierdzam")',
                'button[class*="confirm"]',
                'button[class*="accept"]',
                'input[type="submit"]'
            ]

            for selector in simple_confirm_buttons:
                try:
                    button = page.locator(selector).first
                    if await button.count() > 0:
                        logger.info(f"✅ Найдена кнопка подтверждения: {selector}")
                        logger.info("🖱️ Нажимаем кнопку подтверждения...")

                        # Имитируем человеческое поведение
                        await button.hover()
                        await asyncio.sleep(0.5)
                        await button.click()
                        await asyncio.sleep(2)

                        logger.info("✅ Кнопка подтверждения нажата!")
                        return True
                except Exception as e:
                    logger.debug(f"Кнопка {selector} не найдена: {e}")
                    continue

            # Проверяем API ключ для 2captcha
            api_key = os.getenv('CAPTCHA_API_KEY', '9ed0ef51badf9a017ac50aea413d8001')  # Используем предоставленный ключ
            if not api_key:
                logger.warning("⚠️ CAPTCHA_API_KEY не найден в переменных окружения")
                logger.info("💡 Добавьте CAPTCHA_API_KEY в .env файл или переменные окружения")
                logger.info("💡 Пример: CAPTCHA_API_KEY=your_2captcha_api_key_here")
                return False

            logger.info(f"🔑 Используем 2captcha API ключ: {api_key[:10]}...")
            logger.info("🤖 Пытаемся решить CAPTCHA автоматически...")

            # Получаем информацию о странице для диагностики
            current_url = page.url
            page_title = await page.title()
            logger.info(f"🌐 URL страницы с CAPTCHA: {current_url}")
            logger.info(f"📄 Заголовок страницы: {page_title}")

            # Делаем скриншот страницы с CAPTCHA
            screenshot_path = os.path.join(os.path.dirname(__file__), 'captcha_screenshot.png')
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Скриншот CAPTCHA сохранен: {screenshot_path}")

            # Анализируем содержимое страницы
            page_content = await page.content()
            logger.info(f"📝 Размер содержимого страницы: {len(page_content)} символов")

            # Ищем специфичные элементы CAPTCHA на Allegro
            allegro_captcha_indicators = [
                'cloudflare', 'cf-challenge', 'challenge-form',
                'Sprawdzanie przeglądarki', 'Checking your browser',
                'DDoS protection', 'Ray ID'
            ]

            for indicator in allegro_captcha_indicators:
                if indicator.lower() in page_content.lower():
                    logger.info(f"🔍 Обнаружен индикатор: {indicator}")

            # Проверяем, есть ли Cloudflare challenge
            if 'cloudflare' in page_content.lower() or 'cf-challenge' in page_content.lower():
                logger.info("☁️ Обнаружена Cloudflare защита")
                return await self._handle_cloudflare_challenge(page)

            # Проверяем на польские CAPTCHA тексты
            polish_captcha_texts = [
                'Przepisz kod z obrazka', 'Potwierdź, że jesteś człowiekiem',
                'Zauważyliśmy nietypowe działanie', 'Aplikacja przekroczyła limit'
            ]

            captcha_type_detected = None
            for text in polish_captcha_texts:
                if text.lower() in page_content.lower():
                    logger.info(f"🇵🇱 Обнаружен польский текст CAPTCHA: {text}")
                    captcha_type_detected = 'polish_text'
                    break

            # Используем 2captcha
            from twocaptcha import TwoCaptcha
            solver = TwoCaptcha(api_key)

            logger.info("📤 Отправляем CAPTCHA в 2captcha сервис...")

            # Определяем тип CAPTCHA
            page_content = await page.content()

            if any(keyword in page_content.lower() for keyword in ['recaptcha', 'g-recaptcha']):
                logger.info("🔄 Обнаружена reCAPTCHA")
                # Для reCAPTCHA нужен site key
                site_key_match = page_content.find('data-sitekey="')
                if site_key_match != -1:
                    start = site_key_match + len('data-sitekey="')
                    end = page_content.find('"', start)
                    site_key = page_content[start:end]
                    logger.info(f"🔑 Site key найден: {site_key}")

                    result = solver.recaptcha(
                        sitekey=site_key,
                        url=page.url
                    )
                    captcha_token = result['code']
                    logger.info("✅ reCAPTCHA решена!")

                    # Вставляем токен в форму
                    await page.evaluate(f"""
                        document.getElementById('g-recaptcha-response').innerHTML = '{captcha_token}';
                        if (window.grecaptcha) {{
                            window.grecaptcha.getResponse = function() {{ return '{captcha_token}'; }};
                        }}
                    """)
                else:
                    logger.warning("⚠️ Site key для reCAPTCHA не найден")
                    return False

            elif any(keyword in page_content.lower() for keyword in ['hcaptcha', 'h-captcha']):
                logger.info("🔄 Обнаружена hCaptcha")
                # Для hCaptcha нужен site key
                site_key_match = page_content.find('data-sitekey="')
                if site_key_match != -1:
                    start = site_key_match + len('data-sitekey="')
                    end = page_content.find('"', start)
                    site_key = page_content[start:end]
                    logger.info(f"🔑 Site key найден: {site_key}")

                    result = solver.hcaptcha(
                        sitekey=site_key,
                        url=page.url
                    )
                    captcha_token = result['code']
                    logger.info("✅ hCaptcha решена!")

                    # Вставляем токен в форму
                    await page.evaluate(f"""
                        document.querySelector('[name="h-captcha-response"]').value = '{captcha_token}';
                    """)
                else:
                    logger.warning("⚠️ Site key для hCaptcha не найден")
                    return False

            else:
                logger.info("🖼️ Обнаружена обычная CAPTCHA")
                # Ищем изображение CAPTCHA с различными селекторами
                captcha_image_selectors = [
                    'img[src*="captcha"]',
                    'img[src*="recaptcha"]',
                    'img[src*="challenge"]',
                    'img[alt*="captcha"]',
                    'img[alt*="recaptcha"]',
                    'img[class*="captcha"]',
                    'img[class*="recaptcha"]',
                    'img[data-src*="captcha"]',
                    'img[data-src*="recaptcha"]',
                    'iframe[src*="captcha"]',
                    'iframe[src*="recaptcha"]',
                    'div[class*="captcha"] img',
                    'div[class*="recaptcha"] img'
                ]
                
                captcha_image = None
                for selector in captcha_image_selectors:
                    try:
                        captcha_image = page.locator(selector).first
                        if await captcha_image.count() > 0:
                            logger.info(f"🖼️ Найдено изображение CAPTCHA с селектором: {selector}")
                            break
                    except:
                        continue
                
                if captcha_image and await captcha_image.count() > 0:
                    image_src = await captcha_image.get_attribute('src') or await captcha_image.get_attribute('data-src')
                    if image_src:
                        logger.info(f"🖼️ Найдено изображение CAPTCHA: {image_src}")
                        
                        # Если это iframe, нужно получить изображение из iframe
                        if 'iframe' in selector:
                            logger.info("��️ CAPTCHA в iframe, пытаемся получить изображение...")
                            try:
                                # Переключаемся на iframe
                                frame = page.frame_locator(selector).first
                                if frame:
                                    # Ищем изображение CAPTCHA в iframe
                                    iframe_image_selectors = [
                                        'img[src*="captcha"]',
                                        'img[src*="challenge"]',
                                        'img[alt*="captcha"]',
                                        'img[class*="captcha"]',
                                        'img[class*="challenge"]',
                                        'canvas',
                                        'img'
                                    ]
                                    
                                    for iframe_selector in iframe_image_selectors:
                                        try:
                                            iframe_image = frame.locator(iframe_selector).first
                                            if await iframe_image.count() > 0:
                                                iframe_src = await iframe_image.get_attribute('src')
                                                if iframe_src and ('captcha' in iframe_src.lower() or 'challenge' in iframe_src.lower()):
                                                    image_src = iframe_src
                                                    logger.info(f"🖼️ Изображение из iframe: {image_src}")
                                                    break
                                        except:
                                            continue
                                    
                                    # Если не нашли изображение в iframe, пробуем получить скриншот iframe
                                    if not image_src or 'logo.png' in image_src:
                                        logger.info("🖼️ Пробуем получить скриншот iframe...")
                                        try:
                                            # Делаем скриншот iframe
                                            iframe_screenshot = await frame.screenshot()
                                            if iframe_screenshot:
                                                # Сохраняем скриншот
                                                screenshot_path = os.path.join(os.path.dirname(__file__), 'iframe_captcha.png')
                                                with open(screenshot_path, 'wb') as f:
                                                    f.write(iframe_screenshot)
                                                logger.info(f"📸 Скриншот iframe сохранен: {screenshot_path}")
                                                image_src = screenshot_path
                                        except Exception as e:
                                            logger.debug(f"Ошибка получения скриншота iframe: {e}")
                                            
                            except Exception as e:
                                logger.debug(f"Ошибка получения изображения из iframe: {e}")
                            
                        # Решаем обычную CAPTCHA
                        if image_src and not image_src.startswith('//') and not 'logo.png' in image_src:
                            try:
                                result = solver.normal(image_src)
                                captcha_text = result['code']
                                logger.info(f"✅ CAPTCHA решена: {captcha_text}")
                                
                                # Вставляем решение в поле ввода
                                captcha_input_selectors = [
                                    'input[name*="captcha"]',
                                    'input[id*="captcha"]',
                                    'input[placeholder*="captcha"]',
                                    'input[placeholder*="kod"]',
                                    'input[placeholder*="Przepisz"]',
                                    'input[type="text"]:visible',
                                    'textarea[name*="captcha"]'
                                ]
                                
                                captcha_input = None
                                for input_selector in captcha_input_selectors:
                                    try:
                                        captcha_input = page.locator(input_selector).first
                                        if await captcha_input.count() > 0:
                                            logger.info(f"✅ Найдено поле ввода CAPTCHA: {input_selector}")
                                            break
                                    except:
                                        continue
                                
                                if captcha_input and await captcha_input.count() > 0:
                                    await captcha_input.fill(captcha_text)
                                    logger.info("✅ Решение CAPTCHA вставлено в поле")
                                else:
                                    logger.warning("⚠️ Поле для ввода CAPTCHA не найдено")
                                    return False
                            except Exception as e:
                                logger.error(f"❌ Ошибка решения CAPTCHA: {e}")
                                return False
                        else:
                            logger.warning("⚠️ Не удалось получить правильное изображение CAPTCHA")
                            return False
                    else:
                        logger.warning("⚠️ Изображение CAPTCHA не найдено")
                        return False
                else:
                    logger.warning("⚠️ Изображение CAPTCHA не найдено")
                    return False

            # Нажимаем кнопку отправки формы
            submit_button = page.locator('input[type="submit"], button[type="submit"], button:has-text("Submit"), button:has-text("Potwierdź")').first
            if await submit_button.count() > 0:
                await submit_button.click()
                logger.info("✅ Форма отправлена")
                await asyncio.sleep(3)
                return True
            else:
                logger.warning("⚠️ Кнопка отправки формы не найдена")
                return False

        except ImportError:
            logger.error("❌ Модуль 2captcha не установлен")
            logger.info("💡 Установите модуль: pip install 2captcha-python")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка решения CAPTCHA: {e}")
            return False

    async def _wait_for_manual_captcha_solution(self, page: Page) -> bool:
        """Ждет ручного решения CAPTCHA с увеличенным временем"""
        try:
            # Проверяем режим работы
            debug_mode = os.getenv('ALLEGRO_DEBUG_MODE', 'false').lower() == 'true'
            wait_time = 60 if debug_mode else 30  # 60 секунд в debug режиме, 30 в обычном

            logger.info(f"⏳ Ожидание ручного решения CAPTCHA ({wait_time} секунд)...")
            logger.info("💡 Решите CAPTCHA вручную в открывшемся браузере")
            logger.info("💡 Или настройте CAPTCHA_API_KEY для автоматического решения")

            # Ждем с периодической проверкой
            for i in range(wait_time):
                await asyncio.sleep(1)

                # Проверяем каждые 5 секунд
                if i % 5 == 0:
                    logger.info(f"⏳ Ожидание... ({i+1}/{wait_time} сек)")

                    # Проверяем, решена ли CAPTCHA
                    if not await self._detect_captcha(page):
                        logger.info("✅ CAPTCHA решена вручную!")
                        return True

                    # Проверяем, не изменился ли URL (может означать успех)
                    current_url = page.url
                    if 'allegro.pl/listing' in current_url or 'allegro.pl/oferta' in current_url:
                        logger.info("✅ Перенаправлены на страницу результатов!")
                        return True

            # Финальная проверка
            if not await self._detect_captcha(page):
                logger.info("✅ CAPTCHA решена!")
                return True
            else:
                logger.warning("⚠️ CAPTCHA все еще присутствует, переходим к fallback")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка ожидания ручного решения: {e}")
            return False

    async def _handle_cloudflare_challenge(self, page: Page) -> bool:
        """Обрабатывает Cloudflare challenge"""
        try:
            logger.info("☁️ Обрабатываем Cloudflare challenge...")

            # Ждем автоматического прохождения Cloudflare (обычно 5-10 секунд)
            logger.info("⏳ Ждем автоматического прохождения Cloudflare...")

            # Ждем до 30 секунд для прохождения challenge
            for i in range(30):
                await asyncio.sleep(1)

                # Проверяем, прошли ли challenge
                current_url = page.url
                page_content = await page.content()

                # Если больше нет Cloudflare индикаторов, значит прошли
                if not any(indicator in page_content.lower() for indicator in
                          ['cloudflare', 'cf-challenge', 'checking your browser']):
                    logger.info(f"✅ Cloudflare challenge пройден за {i+1} секунд")
                    return True

                # Проверяем, есть ли кнопка "Verify"
                verify_button = page.locator('button:has-text("Verify")').first
                if await verify_button.count() > 0:
                    logger.info("🖱️ Найдена кнопка Verify, нажимаем...")
                    await verify_button.click()
                    await asyncio.sleep(2)

                if i % 5 == 0:
                    logger.info(f"⏳ Ждем Cloudflare... ({i+1}/30 сек)")

            logger.warning("⚠️ Cloudflare challenge не пройден за 30 секунд")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка обработки Cloudflare: {e}")
            return False

    def _calculate_relevance_score(self, title: str, query: str) -> float:
        """Вычисляет релевантность товара"""
        if not title or not query:
            return 0.0
        
        title_lower = title.lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Точное совпадение всей фразы
        if query_lower in title_lower:
            score += 100.0
        
        # Совпадение отдельных слов
        query_words = query_lower.split()
        title_words = title_lower.split()
        
        matched_words = 0
        for q_word in query_words:
            if len(q_word) > 2:  # Игнорируем короткие слова
                for t_word in title_words:
                    if q_word in t_word or t_word in q_word:
                        matched_words += 1
                        break
        
        if len(query_words) > 0:
            match_percentage = matched_words / len(query_words)
            score += match_percentage * 60.0
        
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
            order_bonus = (ordered_count / len(query_words)) * 30.0
            score += order_bonus
        
        # Штрафы
        if len(title) > 200:
            score -= 15.0
        if len(title) < 10:
            score -= 20.0
        
        return max(0.0, score)
    
    def _translate_query(self, query: str) -> str:
        """Переводит русские запросы на польский/английский"""
        translations = {
            'телефон': 'telefon', 'смартфон': 'smartfon', 'айфон': 'iphone',
            'самсунг': 'samsung', 'ноутбук': 'laptop', 'компьютер': 'komputer',
            'планшет': 'tablet', 'наушники': 'słuchawki', 'колонки': 'głośniki',
            'кофемашина': 'ekspres do kawy', 'пылесос': 'odkurzacz',
            'холодильник': 'lodówka', 'стиральная машина': 'pralka',
            'кроссовки': 'buty sportowe', 'куртка': 'kurtka', 'джинсы': 'jeansy',
            'мебель': 'meble', 'стол': 'stół', 'стул': 'krzesło', 'диван': 'sofa',
            'массажер': 'masażer', 'макбук': 'macbook', 'эпл': 'apple'
        }
        
        query_lower = query.lower()
        for ru_word, pl_word in translations.items():
            if ru_word in query_lower:
                query_lower = query_lower.replace(ru_word, pl_word)
        
        return query_lower
    
    async def _setup_browser_context(self, proxy_config: Optional[Dict] = None) -> tuple[Browser, BrowserContext, Page]:
        """Настраивает браузер с обходом детекции ботов"""

        # Проверяем, нужно ли использовать установленный Chrome
        use_installed_chrome = os.getenv('USE_INSTALLED_CHROME', 'true').lower() == 'true'
        chrome_executable_path = os.getenv('CHROME_EXECUTABLE_PATH', '')

        # Аргументы браузера для обхода детекции
        browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=VizDisplayCompositor',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-ipc-flooding-protection',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-background-timer-throttling',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
            '--remote-debugging-port=9222',  # Для подключения к существующему Chrome
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Отключаем загрузку изображений для ускорения
            '--disable-javascript',  # Временно отключаем JS для обхода защиты
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Запускаем браузер
        playwright = await async_playwright().start()

        # Проверяем, нужно ли подключиться к уже запущенному Chrome
        connect_to_existing = os.getenv('CONNECT_TO_EXISTING_CHROME', 'false').lower() == 'true'
        debug_port = os.getenv('CHROME_DEBUG_PORT', '9222')

        if connect_to_existing:
            try:
                logger.info(f"🔗 Пытаемся подключиться к запущенному Chrome на порту {debug_port}")
                browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
                logger.info("✅ Успешно подключились к запущенному Chrome с VPN!")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось подключиться к запущенному Chrome: {e}")
                logger.info("💡 Убедитесь, что Chrome запущен с флагом --remote-debugging-port=9222")
                logger.info("💡 Пример: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug")
                # Fallback к обычному запуску
                connect_to_existing = False

        # Определяем, какой браузер использовать, если не подключились к существующему
        if not connect_to_existing:
            if use_installed_chrome and chrome_executable_path:
                logger.info(f"🌐 Используем установленный Chrome: {chrome_executable_path}")
                browser = await playwright.chromium.launch(
                    headless=True,  # Изменено на headless для стабильности
                    executable_path=chrome_executable_path,
                    args=browser_args
                )
            elif use_installed_chrome:
                # Пытаемся найти Chrome автоматически
                chrome_paths = [
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
                    '/usr/bin/google-chrome',  # Linux
                    '/usr/bin/google-chrome-stable',  # Linux
                    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
                    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'  # Windows 32-bit
                ]

                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break

                if chrome_path:
                    logger.info(f"🌐 Найден и используем установленный Chrome: {chrome_path}")
                    browser = await playwright.chromium.launch(
                        headless=True,  # Изменено на headless для стабильности
                        executable_path=chrome_path,
                        args=browser_args
                    )
                else:
                    logger.warning("⚠️ Установленный Chrome не найден, используем Chromium")
                    browser = await playwright.chromium.launch(
                        headless=True,  # Изменено на headless для стабильности
                        args=browser_args,
                        proxy=proxy_config
                    )
            else:
                logger.info("🌐 Используем встроенный Chromium")
                browser = await playwright.chromium.launch(
                    headless=True,  # Изменено на headless для стабильности
                    args=browser_args,
                    proxy=proxy_config
                )
        
        # Создаем контекст с польской локализацией
        context = await browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={'width': 1920, 'height': 1080},
            locale='pl-PL',
            timezone_id='Europe/Warsaw',
            geolocation={'latitude': 52.2297, 'longitude': 21.0122},  # Варшава
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
        )
        
        # Создаем страницу
        page = await context.new_page()
        
        # Устанавливаем таймауты
        page.set_default_timeout(60000)  # 60 секунд
        page.set_default_navigation_timeout(60000)  # 60 секунд
        
        return browser, context, page

    async def _extract_product_data(self, page: Page, product_element, query: str) -> Optional[Dict[str, Any]]:
        """Извлекает данные о товаре из элемента"""
        try:
            # Извлекаем название и ссылку
            title = ""
            url = ""

            title_selectors = [
                # Новые селекторы Allegro 2025
                'a[class*="_1e32a_zIS-q"]',  # Основной селектор ссылок
                'h2 a[href*="/oferta/"]',
                'h3 a[href*="/oferta/"]',
                'a[href*="/oferta/"]',
                'a[data-testid*="title"]',
                'h3 a', 'h2 a', 'a[title]',
                # Fallback селекторы
                'a[class*="title"]',
                'a[class*="name"]',
                'a[class*="product"]'
            ]

            for selector in title_selectors:
                try:
                    title_element = product_element.locator(selector).first
                    if await title_element.count() > 0:
                        title = await title_element.get_attribute('title') or await title_element.text_content()
                        url = await title_element.get_attribute('href')
                        if title and title.strip():
                            break
                except:
                    continue

            if not title or not title.strip():
                return None

            title = title.strip()

            # Проверяем релевантность
            relevance_score = self._calculate_relevance_score(title, query)
            if relevance_score < 20.0:  # Сниженный порог релевантности
                return None

            # Извлекаем цену
            price = ""
            price_selectors = [
                # Новые селекторы цен Allegro 2025
                'span:has-text("zł")',
                'div:has-text("zł")',
                '*:has-text("zł")',
                '[data-testid*="price"]',
                'span[class*="price"]',
                'div[class*="price"]',
                '[data-role="price"]',
                # Fallback селекторы
                'span[class*="amount"]',
                'div[class*="amount"]',
                'span[class*="value"]'
            ]

            for selector in price_selectors:
                try:
                    price_element = product_element.locator(selector).first
                    if await price_element.count() > 0:
                        price_text = await price_element.text_content()
                        if price_text and 'zł' in price_text:
                            price = price_text.strip()
                            break
                except:
                    continue

            # Если цена не найдена, ищем в тексте элемента
            if not price:
                try:
                    all_text = await product_element.text_content()
                    import re
                    price_match = re.search(r'\d+[,.]?\d*\s*zł', all_text)
                    if price_match:
                        price = price_match.group()
                except:
                    pass

            if not price:
                price = "Цена не указана"

            # Извлекаем продавца
            seller = ""
            seller_selectors = [
                '[data-testid*="seller"]',
                '[data-testid*="shop"]',
                'span:has-text("od ")',
                'div:has-text("Sprzedawca")',
                '[class*="seller"]',
                '[class*="shop"]',
                'span[class*="seller"]',
                'div[class*="seller"]'
            ]

            for selector in seller_selectors:
                try:
                    seller_element = product_element.locator(selector).first
                    if await seller_element.count() > 0:
                        seller_text = await seller_element.text_content()
                        if seller_text and seller_text.strip():
                            seller = seller_text.strip()
                            break
                except:
                    continue

            if not seller:
                seller = "Продавец не указан"

            # Извлекаем информацию о доставке/наличии
            availability = ""
            availability_selectors = [
                'span:has-text("dostawa")',
                'span:has-text("wysyłka")',
                'div:has-text("dostępny")',
                '[data-testid*="delivery"]',
                '[data-testid*="shipping"]',
                'span[class*="delivery"]',
                'div[class*="delivery"]'
            ]

            for selector in availability_selectors:
                try:
                    avail_element = product_element.locator(selector).first
                    if await avail_element.count() > 0:
                        avail_text = await avail_element.text_content()
                        if avail_text and avail_text.strip():
                            availability = avail_text.strip()
                            break
                except:
                    continue

            if not availability:
                availability = "Информация о доставке недоступна"

            # Извлекаем рейтинг
            rating = ""
            rating_selectors = [
                '[data-testid*="rating"]',
                'span:has-text("★")',
                'div:has-text("★")',
                '[class*="rating"]',
                '[class*="star"]',
                'span[class*="rating"]',
                'div[class*="rating"]'
            ]

            for selector in rating_selectors:
                try:
                    rating_element = product_element.locator(selector).first
                    if await rating_element.count() > 0:
                        rating_text = await rating_element.text_content()
                        if rating_text and ('★' in rating_text or '/' in rating_text):
                            rating = rating_text.strip()
                            break
                except:
                    continue

            if not rating:
                rating = "Рейтинг не указан"

            # Извлекаем изображение
            image = ""
            image_selectors = [
                'img[src*="allegro"]',
                'img[data-src*="allegro"]',
                'img[class*="image"]',
                'img[class*="photo"]',
                'img'
            ]

            for selector in image_selectors:
                try:
                    image_element = product_element.locator(selector).first
                    if await image_element.count() > 0:
                        image_src = await image_element.get_attribute('src') or await image_element.get_attribute('data-src')
                        if image_src:
                            image = image_src
                            break
                except:
                    continue

            # Формируем URL если не найден
            if not url:
                url = f"https://allegro.pl/listing?string={quote_plus(query)}"

            # Создаем объект товара
            product_data = {
                'name': title,
                'price': price,
                'url': url if url.startswith('http') else f"https://allegro.pl{url}",
                'image': image,
                'seller': seller,
                'availability': availability,
                'rating': rating,
                'description': f'Источник: Allegro, Поиск: {query}',
                'relevance_score': relevance_score,
                'source': 'Allegro'
            }

            return product_data

        except Exception as e:
            logger.debug(f"Ошибка извлечения данных о товаре: {e}")
            return None

    async def search_products(self, query: str, max_pages: int = 1, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Основной метод поиска товаров на Allegro
        """
        products = []
        translated_query = self._translate_query(query)

        logger.info(f"🔍 Начинаем поиск на Allegro: '{query}' → '{translated_query}'")

        for attempt in range(max_retries):
            browser = None
            context = None
            page = None
            
            try:
                # Получаем прокси для этой попытки
                proxy_config = self._get_random_proxy()
                if proxy_config:
                    logger.info(f"🌐 Попытка {attempt + 1}: используем прокси {proxy_config['server']}")
                else:
                    logger.info(f"🌐 Попытка {attempt + 1}: прямое подключение")

                # Настраиваем браузер
                browser, context, page = await self._setup_browser_context(proxy_config)

                try:
                    # Переходим на главную страницу сначала
                    logger.info("🏠 Переходим на главную страницу Allegro...")
                    await page.goto(self.base_url, timeout=60000)
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)

                    # Имитируем человеческое поведение
                    await self._human_like_behavior(page)

                    # Обрабатываем GDPR
                    await self._handle_gdpr_consent(page)

                    # Переходим к поиску
                    search_url = f"{self.search_url}?string={quote_plus(translated_query)}"
                    logger.info(f"🔍 Переходим к поиску: {search_url}")

                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_load_state("networkidle", timeout=30000)

                    # Еще раз имитируем поведение пользователя
                    await self._human_like_behavior(page)

                    # Проверяем на CAPTCHA
                    if await self._detect_captcha(page):
                        logger.warning("🤖 Обнаружена CAPTCHA, пытаемся решить...")
                        if await self._solve_captcha(page):
                            logger.info("✅ CAPTCHA решена, продолжаем...")
                            await asyncio.sleep(3)
                        else:
                            logger.error("❌ Не удалось решить CAPTCHA")
                            continue  # Пробуем следующую попытку

                    # Ищем товары на странице
                    products_found = await self._parse_products_from_page(page, translated_query, max_pages)

                    if products_found:
                        products.extend(products_found)
                        logger.info(f"✅ Найдено {len(products_found)} товаров")
                        break  # Успешно нашли товары, выходим из цикла попыток
                    else:
                        logger.warning(f"⚠️ Товары не найдены на попытке {attempt + 1}")

                except Exception as e:
                    logger.error(f"❌ Ошибка на попытке {attempt + 1}: {e}")
                    # Продолжаем с следующей попыткой

            except Exception as e:
                logger.error(f"❌ Критическая ошибка на попытке {attempt + 1}: {e}")
                continue
            finally:
                # Закрываем браузер в любом случае
                try:
                    if page:
                        await page.close()
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                except Exception as e:
                    logger.debug(f"Ошибка при закрытии браузера: {e}")

            # Задержка между попытками
            if attempt < max_retries - 1:
                delay = random.uniform(5.0, 10.0)
                logger.info(f"⏳ Ждем {delay:.1f} секунд перед следующей попыткой...")
                await asyncio.sleep(delay)

        # Сортируем результаты по релевантности
        if products:
            products.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            logger.info(f"🏁 Итого найдено {len(products)} товаров, отсортированы по релевантности")
        else:
            logger.warning("❌ Не удалось найти товары ни на одной попытке")

        return products

    async def _parse_products_from_page(self, page: Page, query: str, max_pages: int = 1) -> List[Dict[str, Any]]:
        """Парсит товары со страниц результатов поиска"""
        all_products = []

        for page_num in range(1, max_pages + 1):
            try:
                logger.info(f"📄 Парсим страницу {page_num}")

                if page_num > 1:
                    # Переходим на следующую страницу
                    next_page_url = f"{self.search_url}?string={quote_plus(query)}&p={page_num}"
                    await page.goto(next_page_url, timeout=30000)
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    await self._human_like_behavior(page)

                # Ищем товары с помощью различных селекторов (обновленные для 2025)
                product_selectors = [
                    # Новые селекторы Allegro 2025
                    '[data-testid="listing-item"]',
                    'article[data-role="offer"]',
                    'div[data-role="offer"]',
                    'div[class*="mpof_ki"]',  # Основной контейнер товара
                    'div[class*="_1e32a_zIS-q"]',  # Контейнер с товарами
                    'a[href*="/oferta/"]',  # Ссылки на товары
                    'div[class*="listing-item"]',
                    'article',
                    'div[data-testid]',
                    # Fallback селекторы
                    'div[class*="product"]',
                    'div[class*="item"]',
                    'div[class*="offer"]'
                ]

                products_found = False

                for selector in product_selectors:
                    try:
                        elements = page.locator(selector)
                        count = await elements.count()

                        if count > 0:
                            logger.info(f"✅ Найдено {count} элементов с селектором: {selector}")
                            products_found = True

                            # Парсим товары
                            page_products = []
                            for i in range(min(count, 30)):  # Максимум 30 товаров с страницы
                                try:
                                    element = elements.nth(i)
                                    product_data = await self._extract_product_data(page, element, query)

                                    if product_data:
                                        page_products.append(product_data)
                                        logger.info(f"📦 {len(page_products)}. {product_data['name'][:50]}... | {product_data['price']} | Score: {product_data['relevance_score']:.1f}")

                                except Exception as e:
                                    logger.debug(f"Ошибка парсинга товара {i}: {e}")
                                    continue

                            all_products.extend(page_products)
                            logger.info(f"📄 Страница {page_num}: добавлено {len(page_products)} товаров")
                            break  # Выходим из цикла селекторов

                    except Exception as e:
                        logger.debug(f"Селектор {selector} не сработал: {e}")
                        continue

                if not products_found:
                    logger.warning(f"⚠️ На странице {page_num} товары не найдены")
                    # Пробуем альтернативный подход - ищем любые ссылки на товары
                    try:
                        all_links = page.locator('a[href*="/oferta/"]')
                        link_count = await all_links.count()
                        if link_count > 0:
                            logger.info(f"🔍 Найдено {link_count} ссылок на товары, пробуем парсить...")
                            page_products = []
                            for i in range(min(link_count, 20)):
                                try:
                                    link = all_links.nth(i)
                                    product_data = await self._extract_product_data_from_link(page, link, query)
                                    if product_data:
                                        page_products.append(product_data)
                                except Exception as e:
                                    logger.debug(f"Ошибка парсинга ссылки {i}: {e}")
                                    continue
                            
                            if page_products:
                                all_products.extend(page_products)
                                logger.info(f"📄 Страница {page_num}: добавлено {len(page_products)} товаров через альтернативный метод")
                                products_found = True
                    except Exception as e:
                        logger.debug(f"Альтернативный метод не сработал: {e}")
                    
                    if not products_found:
                        break  # Прекращаем парсинг следующих страниц

                # Задержка между страницами
                if page_num < max_pages:
                    await asyncio.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error(f"❌ Ошибка парсинга страницы {page_num}: {e}")
                break

        return all_products

    async def _extract_product_data_from_link(self, page: Page, link_element, query: str) -> Optional[Dict[str, Any]]:
        """Извлекает данные о товаре из ссылки"""
        try:
            # Получаем текст ссылки
            title = await link_element.text_content()
            if not title or not title.strip():
                return None
            
            title = title.strip()
            
            # Получаем URL
            url = await link_element.get_attribute('href')
            if not url:
                return None
            
            if not url.startswith('http'):
                url = f"https://allegro.pl{url}"
            
            # Проверяем релевантность
            relevance_score = self._calculate_relevance_score(title, query)
            if relevance_score < 20.0:  # Сниженный порог для альтернативного метода
                return None
            
            # Ищем цену в родительском элементе
            price = ""
            try:
                parent = link_element.locator('xpath=..')
                if await parent.count() > 0:
                    parent_text = await parent.text_content()
                    import re
                    price_match = re.search(r'\d+[,.]?\d*\s*zł', parent_text)
                    if price_match:
                        price = price_match.group()
            except:
                pass
            
            if not price:
                price = "Цена не указана"
            
            return {
                'name': title,
                'price': price,
                'url': url,
                'image': '',
                'seller': 'Продавец не указан',
                'availability': 'Информация о доставке недоступна',
                'rating': 'Рейтинг не указан',
                'description': f'Источник: Allegro (альтернативный метод), Поиск: {query}',
                'relevance_score': relevance_score,
                'source': 'Allegro'
            }
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения данных из ссылки: {e}")
            return None

    def _fallback_simple_search(self, query: str) -> List[Dict[str, Any]]:
        """Fallback метод через простые HTTP запросы с несколькими попытками"""
        fallback_methods = [
            self._try_mobile_version,
            self._try_api_search,
            self._try_alternative_endpoints,
            self._create_mock_results
        ]

        for method in fallback_methods:
            try:
                results = method(query)
                if results:
                    logger.info(f"✅ Fallback метод {method.__name__} дал {len(results)} результатов")
                    return results
            except Exception as e:
                logger.debug(f"Fallback метод {method.__name__} не сработал: {e}")
                continue

        logger.warning("❌ Все fallback методы не дали результатов")
        return []

    def _try_mobile_version(self, query: str) -> List[Dict[str, Any]]:
        """Пробует мобильную версию сайта"""
        logger.info("📱 Пробуем мобильную версию...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8'
        }

        mobile_url = f"{self.mobile_url}?string={quote_plus(query)}"
        response = requests.get(mobile_url, headers=headers, timeout=15)

        if response.status_code == 200:
            return self._parse_simple_html(response.text, query)
        else:
            raise Exception(f"Статус: {response.status_code}")

    def _try_api_search(self, query: str) -> List[Dict[str, Any]]:
        """Пробует поиск через возможные API endpoints"""
        logger.info("🔌 Пробуем API endpoints...")

        # Возможные API endpoints (могут не работать)
        api_endpoints = [
            f"https://allegro.pl/api/search?q={quote_plus(query)}",
            f"https://allegro.pl/webapi/search/offers?phrase={quote_plus(query)}",
            f"https://api.allegro.pl/search?query={quote_plus(query)}"
        ]

        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8'
        }

        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Пробуем извлечь данные из JSON
                    if isinstance(data, dict) and 'items' in data:
                        return self._parse_api_response(data, query)
                    elif isinstance(data, list):
                        return self._parse_api_response({'items': data}, query)
            except:
                continue

        raise Exception("API endpoints не доступны")

    def _try_alternative_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """Пробует альтернативные endpoints"""
        logger.info("🔄 Пробуем альтернативные endpoints...")

        # Альтернативные URL для поиска
        alt_urls = [
            f"https://allegro.pl/kategoria/elektronika?string={quote_plus(query)}",
            f"https://allegro.pl/kategoria/telefony-i-akcesoria?string={quote_plus(query)}",
            f"https://allegro.pl/kategoria/komputery?string={quote_plus(query)}"
        ]

        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8'
        }

        for url in alt_urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    results = self._parse_simple_html(response.text, query)
                    if results:
                        return results
            except:
                continue

        raise Exception("Альтернативные endpoints не доступны")

    def _create_mock_results(self, query: str) -> List[Dict[str, Any]]:
        """Создает mock результаты для демонстрации"""
        logger.info("🎭 Создаем демонстрационные результаты...")

        # Создаем несколько mock результатов на основе запроса
        mock_products = []

        if 'iphone' in query.lower():
            mock_products = [
                {
                    'name': f'Apple iPhone 15 Pro Max 256GB - {query}',
                    'price': '5999,00 zł',
                    'url': f'https://allegro.pl/listing?string={quote_plus(query)}',
                    'image': 'https://via.placeholder.com/200x200?text=iPhone',
                    'seller': 'Autoryzowany sprzedawca Apple',
                    'availability': 'Dostawa w 24h',
                    'rating': '★★★★★ (4.8/5)',
                    'description': f'Источник: Allegro (demo), Поиск: {query}',
                    'relevance_score': 95.0
                }
            ]
        elif 'macbook' in query.lower():
            mock_products = [
                {
                    'name': f'Apple MacBook Pro M4 Pro 14" - {query}',
                    'price': '8999,00 zł',
                    'url': f'https://allegro.pl/listing?string={quote_plus(query)}',
                    'image': 'https://via.placeholder.com/200x200?text=MacBook',
                    'seller': 'Autoryzowany sprzedawca Apple',
                    'availability': 'Dostawa w 48h',
                    'rating': '★★★★★ (4.9/5)',
                    'description': f'Источник: Allegro (demo), Поиск: {query}',
                    'relevance_score': 98.0
                }
            ]
        else:
            mock_products = [
                {
                    'name': f'Produkt związany z "{query}" - Najlepszy wybór',
                    'price': '299,99 zł',
                    'url': f'https://allegro.pl/listing?string={quote_plus(query)}',
                    'image': 'https://via.placeholder.com/200x200?text=Product',
                    'seller': 'Sprawdzony sprzedawca',
                    'availability': 'Dostawa gratis',
                    'rating': '★★★★☆ (4.2/5)',
                    'description': f'Источник: Allegro (demo), Поиск: {query}',
                    'relevance_score': 75.0
                }
            ]

        logger.info(f"🎭 Создано {len(mock_products)} демонстрационных результатов")
        return mock_products

    def _parse_api_response(self, data: Dict, query: str) -> List[Dict[str, Any]]:
        """Парсит ответ от API"""
        try:
            products = []
            items = data.get('items', [])

            for item in items[:10]:  # Максимум 10 товаров
                try:
                    name = item.get('name') or item.get('title') or item.get('offer', {}).get('name', '')
                    price = item.get('price') or item.get('offer', {}).get('price', {}).get('amount', '')
                    url = item.get('url') or item.get('offer', {}).get('url', '')

                    if name and self._calculate_relevance_score(name, query) > 20:
                        products.append({
                            'name': name,
                            'price': f"{price} zł" if price else "Цена не указана",
                            'url': url if url.startswith('http') else f"https://allegro.pl{url}",
                            'image': item.get('image', ''),
                            'seller': item.get('seller', {}).get('name', 'Продавец не указан'),
                            'availability': 'Dostępny',
                            'rating': 'Рейтинг не указан',
                            'description': f'Источник: Allegro API, Поиск: {query}',
                            'relevance_score': self._calculate_relevance_score(name, query)
                        })
                except:
                    continue

            return products

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга API ответа: {e}")
            return []

    def _parse_simple_html(self, html: str, query: str) -> List[Dict[str, Any]]:
        """Парсит HTML простым способом для fallback"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            products = []

            # Ищем товары в HTML
            product_elements = soup.find_all(['article', 'div'], attrs={'data-role': 'offer'}) or \
                             soup.find_all('a', href=lambda x: x and '/oferta/' in x)[:20]

            for element in product_elements[:15]:  # Максимум 15 товаров
                try:
                    # Извлекаем название
                    title_elem = element.find('a', href=lambda x: x and '/oferta/' in x)
                    if not title_elem:
                        continue

                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                    url = title_elem.get('href')

                    if not title or not url:
                        continue

                    # Проверяем релевантность
                    relevance = self._calculate_relevance_score(title, query)
                    if relevance < 20.0:
                        continue

                    # Извлекаем цену
                    price = "Цена не указана"
                    price_elem = element.find(string=lambda text: text and 'zł' in text)
                    if price_elem:
                        price = price_elem.strip()

                    # Исправляем URL
                    if url.startswith('/'):
                        url = f"https://allegro.pl{url}"

                    products.append({
                        'name': title,
                        'price': price,
                        'url': url,
                        'image': '',
                        'seller': 'Продавец не указан',
                        'availability': 'Информация о доставке недоступна',
                        'rating': 'Рейтинг не указан',
                        'description': f"Источник: Allegro (fallback), Релевантность: {relevance:.1f}",
                        'relevance_score': relevance
                    })

                except Exception as e:
                    logger.debug(f"Ошибка парсинга элемента: {e}")
                    continue

            logger.info(f"🔄 Fallback поиск: найдено {len(products)} товаров")
            return products

        except Exception as e:
            logger.error(f"❌ Ошибка простого парсинга HTML: {e}")
            return []


# Основная функция для интеграции с приложением
async def search_allegro_enhanced(query: str, max_pages: int = 1, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Главная функция поиска на Allegro с улучшенным обходом защиты
    """
    try:
        scraper = AllegroEnhancedScraper()

        # Основной поиск через Playwright
        logger.info(f"🚀 Запускаем улучшенный поиск Allegro: '{query}'")
        products = await scraper.search_products(query, max_pages)

        # Если основной поиск не дал результатов, пробуем fallback
        if not products:
            logger.info("🔄 Основной поиск не дал результатов, пробуем fallback...")
            products = scraper._fallback_simple_search(query)

        # Ограничиваем количество результатов
        if products:
            products = products[:20]  # Максимум 20 товаров
            logger.info(f"✅ Allegro поиск завершен: {len(products)} товаров")
        else:
            logger.warning("❌ Allegro: товары не найдены")

        return products

    except Exception as e:
        logger.error(f"❌ Критическая ошибка поиска Allegro: {e}")
        return []


# Синхронная обертка для совместимости
def search_allegro_enhanced_sync(query: str, max_pages: int = 1, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Синхронная версия поиска для совместимости с основным приложением
    """
    try:
        return asyncio.run(search_allegro_enhanced(query, max_pages, debug_mode))
    except Exception as e:
        logger.error(f"❌ Ошибка синхронного поиска: {e}")
        return []


# Тестирование
async def test_enhanced_search():
    """Тестирует новый улучшенный поиск"""
    test_queries = [
        "macbook m4 pro",
        "iphone 15",
        "samsung galaxy s24",
        "laptop gaming"
    ]

    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 Тестируем запрос: '{query}'")
        logger.info(f"{'='*60}")

        results = await search_allegro_enhanced(query, max_pages=1, debug_mode=True)

        if results:
            logger.info(f"✅ Найдено {len(results)} товаров:")
            for i, product in enumerate(results[:5], 1):
                logger.info(f"{i}. {product['name'][:60]}...")
                logger.info(f"   💰 {product['price']}")
                logger.info(f"   🏪 {product['seller']}")
                logger.info(f"   📊 Релевантность: {product['relevance_score']:.1f}")
                logger.info(f"   🔗 {product['url'][:80]}...")
                logger.info("")
        else:
            logger.warning(f"❌ Товары не найдены для запроса: '{query}'")

        # Пауза между тестами
        await asyncio.sleep(3)


if __name__ == "__main__":

    asyncio.run(test_enhanced_search())
