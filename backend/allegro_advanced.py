import requests
import time
import random
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class AllegroAdvancedScraper:
    def __init__(self):
        self.base_url = "https://allegro.pl"
        self.ua = UserAgent()
        self.session = requests.Sessistarton()
        
        # Список бесплатных прокси (можно расширить)
        self.proxies_list = [
            None,  # Без прокси
            # Добавьте рабочие прокси если есть
        ]
        
        # Список User-Agent'ов
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def get_headers(self):
        """Генерация случайных заголовков"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def search_products(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Поиск товаров с улучшенными методами обхода"""
        products = []
        
        try:
            # Кодируем запрос
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"{self.base_url}/listing?string={encoded_query}"
            
            logger.info(f"🔍 Поиск на Allegro: {query}")
            
            # Пробуем разные методы
            for attempt in range(3):
                try:
                    headers = self.get_headers()
                    
                    # Случайная задержка
                    time.sleep(random.uniform(1, 3))
                    
                    response = self.session.get(search_url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        products = self.parse_products(response.text, query, max_results)
                        if products:
                            logger.info(f"✅ Allegro: найдено {len(products)} товаров")
                            return products
                    
                    elif response.status_code == 403:
                        logger.warning(f"Попытка {attempt + 1}: Доступ заблокирован, пробуем другой метод")
                        time.sleep(random.uniform(3, 7))
                        continue
                    
                    else:
                        logger.warning(f"Попытка {attempt + 1}: Статус {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Попытка {attempt + 1} неудачна: {e}")
                    time.sleep(random.uniform(2, 5))
            
            # Если обычный метод не работает, пробуем мобильную версию
            return self.try_mobile_version(query, max_results)
            
        except Exception as e:
            logger.error(f"Ошибка поиска на Allegro: {e}")
            return []
    
    def try_mobile_version(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Попытка через мобильную версию"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            mobile_url = f"https://m.allegro.pl/listing?string={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pl-PL,pl;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                products = self.parse_mobile_products(response.text, query, max_results)
                if products:
                    logger.info(f"✅ Allegro Mobile: найдено {len(products)} товаров")
                    return products
            
        except Exception as e:
            logger.warning(f"Мобильная версия не работает: {e}")
        
        return []
    
    def parse_products(self, html: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Парсинг товаров из HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            # Ищем товары по различным селекторам
            selectors = [
                'article[data-role="offer"]',
                'div[data-role="offer"]',
                '.offer-item',
                '.listing-item',
                '[data-testid="listing-item"]'
            ]
            
            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break
            
            if not items:
                logger.warning("Не найдены товары в HTML")
                return []
            
            for item in items[:max_results]:
                try:
                    product = self.extract_product_info(item)
                    if product and self.is_relevant(product['name'], query):
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Ошибка парсинга товара: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return []
    
    def parse_mobile_products(self, html: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Парсинг товаров из мобильной версии"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            # Мобильные селекторы
            items = soup.select('.listing-item, .offer-item, [data-testid="listing-item"]')
            
            for item in items[:max_results]:
                try:
                    product = self.extract_mobile_product_info(item)
                    if product and self.is_relevant(product['name'], query):
                        products.append(product)
                except Exception as e:
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Ошибка парсинга мобильной версии: {e}")
            return []
    
    def extract_product_info(self, item) -> Dict[str, Any]:
        """Извлечение информации о товаре"""
        try:
            # Название
            name_selectors = [
                'h2 a', '.offer-title a', '[data-testid="listing-item-title"] a',
                '.listing-item-title a', 'a[data-testid="listing-item-title"]'
            ]
            name = ""
            link = ""
            
            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    link = name_elem.get('href', '')
                    break
            
            if not name:
                return None
            
            # Цена
            price_selectors = [
                '.price', '.offer-price', '[data-testid="listing-item-price"]',
                '.listing-item-price', '.price-value'
            ]
            price = "Цена не указана"
            
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price = price_elem.get_text(strip=True)
                    break
            
            # Изображение
            img_selectors = [
                'img', '.offer-image img', '[data-testid="listing-item-image"] img'
            ]
            image = ""
            
            for selector in img_selectors:
                img_elem = item.select_one(selector)
                if img_elem:
                    image = img_elem.get('src', '') or img_elem.get('data-src', '')
                    break
            
            # Формируем полную ссылку
            if link and not link.startswith('http'):
                link = f"https://allegro.pl{link}"
            
            return {
                'name': name,
                'price': price,
                'url': link,
                'image': image,
                'description': name,
                'source': 'allegro'
            }
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения информации: {e}")
            return None
    
    def extract_mobile_product_info(self, item) -> Dict[str, Any]:
        """Извлечение информации о товаре из мобильной версии"""
        return self.extract_product_info(item)  # Используем тот же метод
    
    def is_relevant(self, title: str, query: str) -> bool:
        """Проверка релевантности товара"""
        if not title or not query:
            return False
        
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Простая проверка на наличие слов из запроса
        query_words = query_lower.split()
        matched_words = sum(1 for word in query_words if word in title_lower)
        
        # Товар релевантен если совпадает хотя бы половина слов
        return matched_words >= len(query_words) * 0.5

def search_allegro_advanced(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Основная функция для продвинутого поиска на Allegro"""
    scraper = AllegroAdvancedScraper()
    return scraper.search_products(query, max_results)
