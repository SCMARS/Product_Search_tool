

import pandas as pd
import logging
import re
import json
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz
import time
import os
from datetime import datetime

# Импортируем наши модули поиска
from amazon import search_amazon
from aliexpress import search_aliexpress
from allegro import search_allegro_improved

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductMatcher:
    """
    Класс для поиска товаров по характеристикам из файла
    """
    
    def __init__(self):
        self.results = []
        self.processed_count = 0
        self.total_count = 0
        
    def read_file(self, file_path: str) -> pd.DataFrame:
        """
        Читает файл CSV или Excel и возвращает DataFrame
        """
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Поддерживаются только файлы CSV и Excel")
                
            logger.info(f"Файл загружен: {len(df)} строк, колонки: {list(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка чтения файла: {e}")
            raise
    
    def build_search_query(self, row: pd.Series) -> str:


        query_parts = []
        
        # Основные поля для поиска (в порядке приоритета)
        priority_fields = [
            'brand', 'бренд', 'марка',
            'product_name', 'название', 'name', 'product',
            'model', 'модель',
            'category', 'категория',
            'type', 'тип'
        ]
        
        # Дополнительные характеристики
        additional_fields = [
            'color', 'цвет', 'colour',
            'size', 'размер',
            'material', 'материал',
            'keywords', 'ключевые_слова', 'tags'
        ]
        
        # Собираем основные части запроса
        for field in priority_fields:
            if field in row.index and pd.notna(row[field]) and str(row[field]).strip():
                value = str(row[field]).strip()
                if value.lower() not in ['nan', 'null', '']:
                    query_parts.append(value)
                    
        # Добавляем дополнительные характеристики
        for field in additional_fields:
            if field in row.index and pd.notna(row[field]) and str(row[field]).strip():
                value = str(row[field]).strip()
                if value.lower() not in ['nan', 'null', '']:
                    query_parts.append(value)
        
        # Формируем финальный запрос
        query = ' '.join(query_parts[:5])  # Ограничиваем длину запроса
        
        # Очищаем запрос от лишних символов
        query = re.sub(r'[^\w\s\-]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        logger.info(f"Сформирован запрос: '{query}'")
        return query
    
    def extract_characteristics(self, row: pd.Series) -> Dict:
        """
        Извлекает характеристики товара для фильтрации результатов
        """
        characteristics = {}
        
        # Извлекаем ключевые характеристики
        char_mapping = {
            'brand': ['brand', 'бренд', 'марка'],
            'color': ['color', 'цвет', 'colour'],
            'size': ['size', 'размер'],
            'material': ['material', 'материал'],
            'category': ['category', 'категория'],
            'type': ['type', 'тип'],
            'model': ['model', 'модель']
        }
        
        for char_key, possible_fields in char_mapping.items():
            for field in possible_fields:
                if field in row.index and pd.notna(row[field]):
                    value = str(row[field]).strip()
                    if value.lower() not in ['nan', 'null', '']:
                        characteristics[char_key] = value.lower()
                        break
        
        return characteristics
    
    def calculate_relevance_score(self, product: Dict, query: str, characteristics: Dict) -> float:
        """
        Вычисляет релевантность товара на основе запроса и характеристик
        """
        score = 0.0
        
        title = product.get('name', '').lower()
        description = product.get('description', '').lower()
        
        # Базовая релевантность по названию (40% веса)
        title_score = fuzz.partial_ratio(query.lower(), title) / 100.0
        score += title_score * 0.4
        
        # Релевантность по описанию (20% веса)
        if description:
            desc_score = fuzz.partial_ratio(query.lower(), description) / 100.0
            score += desc_score * 0.2
        
        # Бонусы за совпадение характеристик (40% веса)
        char_bonus = 0.0
        char_count = 0
        
        for char_key, char_value in characteristics.items():
            if char_value:
                char_count += 1
                # Проверяем наличие характеристики в названии или описании
                if char_value in title or char_value in description:
                    char_bonus += 1.0
                elif any(word in title for word in char_value.split()):
                    char_bonus += 0.5
        
        if char_count > 0:
            score += (char_bonus / char_count) * 0.4
        
        return min(score, 1.0)  # Ограничиваем максимальный скор
    
    def filter_relevant_products(self, products: List[Dict], query: str, 
                                characteristics: Dict, min_score: float = 0.3) -> List[Dict]:
        """
        Фильтрует товары по релевантности
        """
        scored_products = []
        
        for product in products:
            score = self.calculate_relevance_score(product, query, characteristics)
            if score >= min_score:
                product['relevance_score'] = score
                scored_products.append(product)
        
        # Сортируем по релевантности
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Отфильтровано {len(scored_products)} из {len(products)} товаров")
        return scored_products[:10]  # Возвращаем топ-10
    
    def search_single_product(self, row: pd.Series, row_index: int) -> Dict:
        """
        Ищет товар по одной строке из файла
        """
        logger.info(f"Обработка строки {row_index + 1}")
        
        # Формируем запрос
        query = self.build_search_query(row)
        if not query:
            logger.warning(f"Не удалось сформировать запрос для строки {row_index + 1}")
            return {
                'row_index': row_index + 1,
                'query': '',
                'error': 'Не удалось сформировать поисковый запрос',
                'amazon': [],
                'aliexpress': [],
                'allegro': []
            }
        
        # Извлекаем характеристики
        characteristics = self.extract_characteristics(row)
        
        result = {
            'row_index': row_index + 1,
            'query': query,
            'characteristics': characteristics,
            'amazon': [],
            'aliexpress': [],
            'allegro': []
        }
        
        # Поиск на Amazon
        try:
            logger.info(f"Поиск на Amazon: {query}")
            amazon_products = search_amazon(query, max_pages=1)
            filtered_amazon = self.filter_relevant_products(amazon_products, query, characteristics)
            result['amazon'] = filtered_amazon
            logger.info(f"Amazon: найдено {len(filtered_amazon)} релевантных товаров")
        except Exception as e:
            logger.error(f"Ошибка поиска на Amazon: {e}")
            result['amazon_error'] = str(e)
        
        # Поиск на AliExpress
        try:
            logger.info(f"Поиск на AliExpress: {query}")
            aliexpress_products = search_aliexpress(query, limit=10)
            filtered_aliexpress = self.filter_relevant_products(aliexpress_products, query, characteristics)
            result['aliexpress'] = filtered_aliexpress
            logger.info(f"AliExpress: найдено {len(filtered_aliexpress)} релевантных товаров")
        except Exception as e:
            logger.error(f"Ошибка поиска на AliExpress: {e}")
            result['aliexpress_error'] = str(e)
        
        # Поиск на Allegro с улучшенными методами
        try:
            logger.info(f"Поиск на Allegro: {query}")
            allegro_products = search_allegro_improved(query, max_pages=1)
            filtered_allegro = self.filter_relevant_products(allegro_products, query, characteristics)
            result['allegro'] = filtered_allegro
            logger.info(f"Allegro: найдено {len(filtered_allegro)} релевантных товаров")
        except Exception as e:
            logger.error(f"Ошибка поиска на Allegro: {e}")
            result['allegro_error'] = str(e)
        
        # Добавляем задержку между запросами
        time.sleep(2)
        
        return result

    def process_file(self, file_path: str, output_file: str = None) -> List[Dict]:
        """
        Обрабатывает весь файл и возвращает результаты с принудительным обновлением
        """
        # Очищаем старые результаты для получения свежих данных
        if output_file and os.path.exists(output_file):
            os.remove(output_file)
            logger.info(f"🗑️ Удален старый файл результатов: {output_file}")

        # Читаем файл
        df = self.read_file(file_path)
        self.total_count = len(df)
        self.processed_count = 0
        self.results = []

        logger.info(f"🔍 Начинаем обработку {self.total_count} товаров с получением свежих данных")

        # Обрабатываем каждую строку
        for index, row in df.iterrows():
            try:
                result = self.search_single_product(row, index)
                self.results.append(result)
                self.processed_count += 1

                logger.info(f"Обработано {self.processed_count}/{self.total_count} товаров")

            except Exception as e:
                logger.error(f"Ошибка обработки строки {index + 1}: {e}")
                error_result = {
                    'row_index': index + 1,
                    'error': str(e),
                    'amazon': [],
                    'aliexpress': [],
                    'allegro': []
                }
                self.results.append(error_result)
                self.processed_count += 1

        # Сохраняем результаты
        if output_file:
            self.save_results(output_file)

        logger.info(f"Обработка завершена. Обработано {self.processed_count} товаров")
        return self.results

    def save_results(self, output_file: str):
        """
        Сохраняет результаты в файл
        """
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

            # Добавляем метаданные
            output_data = {
                'metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'total_products': self.total_count,
                    'processed_products': self.processed_count,
                    'success_rate': f"{(self.processed_count / self.total_count * 100):.1f}%" if self.total_count > 0 else "0%"
                },
                'results': self.results
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Результаты сохранены в {output_file}")

        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")

    def export_to_excel(self, output_file: str):
        """
        Экспортирует результаты в Excel файл
        """
        try:
            # Подготавливаем данные для Excel
            excel_data = []

            for result in self.results:
                row_data = {
                    'Строка': result.get('row_index', ''),
                    'Запрос': result.get('query', ''),
                    'Характеристики': json.dumps(result.get('characteristics', {}), ensure_ascii=False),
                    'Ошибка': result.get('error', '')
                }

                # Добавляем результаты по каждой площадке
                for platform in ['amazon', 'aliexpress', 'allegro']:
                    products = result.get(platform, [])
                    if products:
                        # Берем лучший результат
                        best_product = products[0]
                        row_data[f'{platform.title()}_Название'] = best_product.get('name', '')
                        row_data[f'{platform.title()}_Цена'] = best_product.get('price', '')
                        row_data[f'{platform.title()}_URL'] = best_product.get('url', '')
                        row_data[f'{platform.title()}_Релевантность'] = f"{best_product.get('relevance_score', 0):.2f}"
                    else:
                        row_data[f'{platform.title()}_Название'] = ''
                        row_data[f'{platform.title()}_Цена'] = ''
                        row_data[f'{platform.title()}_URL'] = ''
                        row_data[f'{platform.title()}_Релевантность'] = ''

                excel_data.append(row_data)

            # Создаем DataFrame и сохраняем в Excel
            df = pd.DataFrame(excel_data)
            df.to_excel(output_file, index=False, engine='openpyxl')

            logger.info(f"Результаты экспортированы в Excel: {output_file}")

        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")

    def get_progress(self) -> Dict:
        """
        Возвращает прогресс обработки
        """
        return {
            'total': self.total_count,
            'processed': self.processed_count,
            'percentage': (self.processed_count / self.total_count * 100) if self.total_count > 0 else 0
        }


def create_sample_csv(filename: str = "sample_products.csv"):
    """
    Создает пример CSV файла с характеристиками товаров
    """
    sample_data = [
        {
            'product_name': 'iPhone 15 Pro',
            'brand': 'Apple',
            'category': 'Смартфоны',
            'color': 'Черный',
            'size': '128GB',
            'keywords': 'телефон мобильный айфон'
        },
        {
            'product_name': 'MacBook Air',
            'brand': 'Apple',
            'category': 'Ноутбуки',
            'color': 'Серебристый',
            'size': '13 дюймов',
            'keywords': 'ноутбук лэптоп макбук'
        },
        {
            'product_name': 'Кофемашина',
            'brand': 'DeLonghi',
            'category': 'Бытовая техника',
            'type': 'Автоматическая',
            'keywords': 'кофе эспрессо капучино'
        }
    ]

    df = pd.DataFrame(sample_data)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Создан пример файла: {filename}")


if __name__ == "__main__":
    # Пример использования
    matcher = ProductMatcher()

    # Создаем пример файла
    create_sample_csv()

    # Обрабатываем файл
    results = matcher.process_file("sample_products.csv", "results_detailed.json")

    # Экспортируем в Excel
    matcher.export_to_excel("results_detailed.xlsx")

    print(f"Обработка завершена. Результаты сохранены в results_detailed.json и results_detailed.xlsx")
