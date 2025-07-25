import asyncio
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
import threading
from queue import Queue
import traceback

# Импортируем функции поиска
from allegro import search_allegro_improved as search_allegro
from amazon import search_amazon
from aliexpress import search_aliexpress

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchSearchProcessor:
    def __init__(self, max_workers: int = 10, max_retries: int = 3):
        """
        Инициализация процессора массового поиска
        
        Args:
            max_workers: Максимальное количество параллельных потоков
            max_retries: Максимальное количество попыток для каждого запроса
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.results_queue = Queue()
        self.progress_callback = None
        self.total_queries = 0
        self.processed_queries = 0
        self.failed_queries = 0
        
    def set_progress_callback(self, callback):
        """Установка callback для отслеживания прогресса"""
        self.progress_callback = callback
        
    def update_progress(self, message: str, current: int = None, total: int = None):
        """Обновление прогресса"""
        if current is not None:
            self.processed_queries = current
        if total is not None:
            self.total_queries = total
            
        if self.progress_callback:
            self.progress_callback({
                'message': message,
                'current': self.processed_queries,
                'total': self.total_queries,
                'failed': self.failed_queries,
                'progress': (self.processed_queries / self.total_queries * 100) if self.total_queries > 0 else 0
            })
        
        logger.info(f"Progress: {self.processed_queries}/{self.total_queries} ({self.failed_queries} failed) - {message}")

    def load_queries_from_file(self, filepath: str) -> List[str]:
        """
        Загружает поисковые запросы из файла
        
        Args:
            filepath: Путь к файлу (.csv или .xlsx)
            
        Returns:
            Список поисковых запросов
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise FileNotFoundError(f"Файл не найден: {filepath}")
                
            if filepath.suffix.lower() == '.csv':
                df = pd.read_csv(filepath, encoding='utf-8')
            elif filepath.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {filepath.suffix}")
            
            # Ищем столбец с запросами
            query_columns = ['query', 'product', 'product_name', 'name', 'title', 'search']
            query_column = None
            
            for col in query_columns:
                if col in df.columns:
                    query_column = col
                    break
                    
            if query_column is None:
                available_columns = ', '.join(df.columns)
                raise ValueError(f"Столбец с запросами не найден. Доступные столбцы: {available_columns}")
            
            # Извлекаем запросы
            queries = df[query_column].dropna().astype(str).tolist()
            
            # Удаляем дубликаты и пустые строки
            queries = list(set([q.strip() for q in queries if q.strip()]))
            
            logger.info(f"Загружено {len(queries)} уникальных запросов из файла {filepath}")
            return queries
            
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {filepath}: {str(e)}")
            raise

    def search_single_product(self, query: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Поиск одного товара на всех платформах
        
        Args:
            query: Поисковый запрос
            retry_count: Номер попытки
            
        Returns:
            Результат поиска
        """
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'errors': []
        }
        
        try:
            # Поиск на Amazon
            try:
                amazon_results = search_amazon(query, limit=3)
                if amazon_results:
                    result['platforms']['amazon'] = amazon_results[:3]
                else:
                    result['platforms']['amazon'] = []
            except Exception as e:
                error_msg = f"Amazon error: {str(e)}"
                result['errors'].append(error_msg)
                result['platforms']['amazon'] = []
                logger.warning(f"Ошибка поиска на Amazon для '{query}': {e}")
            
            # Поиск на AliExpress
            try:
                aliexpress_results = search_aliexpress(query, limit=3)
                if aliexpress_results:
                    result['platforms']['aliexpress'] = aliexpress_results[:3]
                else:
                    result['platforms']['aliexpress'] = []
            except Exception as e:
                error_msg = f"AliExpress error: {str(e)}"
                result['errors'].append(error_msg)
                result['platforms']['aliexpress'] = []
                logger.warning(f"Ошибка поиска на AliExpress для '{query}': {e}")
            
            # Поиск на Allegro
            try:
                allegro_results = search_allegro(query, max_pages=1)
                if allegro_results:
                    result['platforms']['allegro'] = allegro_results[:3]
                else:
                    result['platforms']['allegro'] = []
            except Exception as e:
                error_msg = f"Allegro error: {str(e)}"
                result['errors'].append(error_msg)
                result['platforms']['allegro'] = []
                logger.warning(f"Ошибка поиска на Allegro для '{query}': {e}")
            
            # Подсчет общего количества найденных товаров
            total_products = sum(len(products) for products in result['platforms'].values())
            result['total_products_found'] = total_products
            
            return result
            
        except Exception as e:
            error_msg = f"General error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(f"Общая ошибка для запроса '{query}': {e}")
            return result

    def process_queries_batch(self, queries: List[str], batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Обрабатывает запросы батчами для оптимизации памяти
        
        Args:
            queries: Список запросов
            batch_size: Размер батча
            
        Returns:
            Список результатов
        """
        all_results = []
        total_batches = (len(queries) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(queries))
            batch_queries = queries[start_idx:end_idx]
            
            logger.info(f"Обработка батча {batch_num + 1}/{total_batches} ({len(batch_queries)} запросов)")
            self.update_progress(f"Обработка батча {batch_num + 1}/{total_batches}", start_idx, len(queries))
            
            batch_results = self.process_queries_parallel(batch_queries)
            all_results.extend(batch_results)
            
            # Сохраняем промежуточные результаты
            self.save_intermediate_results(all_results, f"batch_{batch_num + 1}")
            
            # Небольшая пауза между батчами
            time.sleep(1)
        
        return all_results

    def process_queries_parallel(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Параллельная обработка запросов
        
        Args:
            queries: Список запросов
            
        Returns:
            Список результатов
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи
            future_to_query = {
                executor.submit(self.search_single_product, query): query 
                for query in queries
            }
            
            # Обрабатываем результаты по мере готовности
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.processed_queries += 1
                    
                    # Обновляем прогресс
                    self.update_progress(f"Обработан запрос: {query[:50]}...")
                    
                except Exception as e:
                    self.failed_queries += 1
                    error_result = {
                        'query': query,
                        'timestamp': datetime.now().isoformat(),
                        'platforms': {},
                        'errors': [f"Processing error: {str(e)}"],
                        'total_products_found': 0
                    }
                    results.append(error_result)
                    logger.error(f"Ошибка обработки запроса '{query}': {e}")
                
                # Небольшая пауза для избежания rate limiting
                time.sleep(0.1)
        
        return results

    def save_intermediate_results(self, results: List[Dict[str, Any]], batch_name: str):
        """Сохранение промежуточных результатов"""
        try:
            filename = f"intermediate_results_{batch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Промежуточные результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения промежуточных результатов: {e}")

    def export_results(self, results: List[Dict[str, Any]], output_file: str, format_type: str = 'auto'):
        """
        Экспорт результатов в различные форматы
        
        Args:
            results: Список результатов
            output_file: Путь к выходному файлу
            format_type: Тип формата ('auto', 'csv', 'excel', 'json')
        """
        try:
            output_path = Path(output_file)
            
            # Определяем формат по расширению файла
            if format_type == 'auto':
                if output_path.suffix.lower() == '.csv':
                    format_type = 'csv'
                elif output_path.suffix.lower() in ['.xlsx', '.xls']:
                    format_type = 'excel'
                elif output_path.suffix.lower() == '.json':
                    format_type = 'json'
                else:
                    format_type = 'excel'  # По умолчанию Excel
            
            if format_type == 'json':
                self._export_to_json(results, output_file)
            elif format_type == 'csv':
                self._export_to_csv(results, output_file)
            elif format_type == 'excel':
                self._export_to_excel(results, output_file)
            else:
                raise ValueError(f"Неподдерживаемый формат: {format_type}")
                
            logger.info(f"Результаты экспортированы в {output_file} ({len(results)} запросов)")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта результатов: {e}")
            raise

    def _export_to_json(self, results: List[Dict[str, Any]], output_file: str):
        """Экспорт в JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def _export_to_csv(self, results: List[Dict[str, Any]], output_file: str):
        """Экспорт в CSV"""
        # Создаем плоскую структуру для CSV
        flat_results = []
        
        for result in results:
            base_row = {
                'query': result['query'],
                'timestamp': result['timestamp'],
                'total_products_found': result.get('total_products_found', 0),
                'errors': '; '.join(result.get('errors', []))
            }
            
            # Добавляем данные по платформам
            for platform, products in result.get('platforms', {}).items():
                for i, product in enumerate(products[:3]):  # Максимум 3 товара с каждой платформы
                    suffix = f"_{i+1}" if i > 0 else ""
                    flat_results.append({
                        **base_row,
                        'platform': platform,
                        f'product_name{suffix}': product.get('name', ''),
                        f'price{suffix}': product.get('price', ''),
                        f'url{suffix}': product.get('url', ''),
                        f'image{suffix}': product.get('image', ''),
                        f'description{suffix}': product.get('description', '')
                    })
            
            # Если нет товаров, добавляем пустую строку
            if not result.get('platforms'):
                flat_results.append(base_row)
        
        df = pd.DataFrame(flat_results)
        df.to_csv(output_file, index=False, encoding='utf-8')

    def _export_to_excel(self, results: List[Dict[str, Any]], output_file: str):
        """Экспорт в Excel с форматированием"""
        # Создаем плоскую структуру как для CSV
        flat_results = []
        
        for result in results:
            base_row = {
                'query': result['query'],
                'timestamp': result['timestamp'],
                'total_products_found': result.get('total_products_found', 0),
                'errors': '; '.join(result.get('errors', []))
            }
            
            # Добавляем данные по платформам
            for platform, products in result.get('platforms', {}).items():
                for i, product in enumerate(products[:3]):
                    suffix = f"_{i+1}" if i > 0 else ""
                    flat_results.append({
                        **base_row,
                        'platform': platform,
                        f'product_name{suffix}': product.get('name', ''),
                        f'price{suffix}': product.get('price', ''),
                        f'url{suffix}': product.get('url', ''),
                        f'image{suffix}': product.get('image', ''),
                        f'description{suffix}': product.get('description', '')
                    })
            
            if not result.get('platforms'):
                flat_results.append(base_row)
        
        df = pd.DataFrame(flat_results)
        
        # Создаем Excel файл с форматированием
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Получаем рабочую книгу для форматирования
            workbook = writer.book
            worksheet = writer.sheets['Results']
            
            # Форматирование заголовков
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
            
            # Автоматическая ширина столбцов
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    def batch_search_from_file(self, input_file: str, output_file: str, max_pages: int = 3, 
                              batch_size: int = 50, format_type: str = 'auto') -> Dict[str, Any]:
        """
        Основная функция массового поиска
        
        Args:
            input_file: Путь к входному файлу
            output_file: Путь к выходному файлу
            max_pages: Максимальное количество страниц для поиска
            batch_size: Размер батча для обработки
            format_type: Тип выходного формата
            
        Returns:
            Статистика обработки
        """
        start_time = time.time()
        
        try:
            # Загружаем запросы
            logger.info(f"Загрузка запросов из файла: {input_file}")
            self.update_progress("Загрузка запросов из файла...", 0, 0)
            
            queries = self.load_queries_from_file(input_file)
            self.total_queries = len(queries)
            
            if not queries:
                raise ValueError("Не найдено запросов для обработки")
            
            logger.info(f"Найдено {len(queries)} запросов для обработки")
            self.update_progress(f"Найдено {len(queries)} запросов", 0, len(queries))
            
            # Обрабатываем запросы
            logger.info("Начинаем обработку запросов...")
            results = self.process_queries_batch(queries, batch_size)
            
            # Экспортируем результаты
            logger.info(f"Экспорт результатов в {output_file}")
            self.update_progress("Экспорт результатов...", len(queries), len(queries))
            
            self.export_results(results, output_file, format_type)
            
            # Подсчитываем статистику
            end_time = time.time()
            processing_time = end_time - start_time
            
            total_products = sum(r.get('total_products_found', 0) for r in results)
            successful_queries = len([r for r in results if not r.get('errors')])
            
            statistics = {
                'total_queries': len(queries),
                'successful_queries': successful_queries,
                'failed_queries': self.failed_queries,
                'total_products_found': total_products,
                'processing_time_seconds': processing_time,
                'average_time_per_query': processing_time / len(queries) if queries else 0,
                'output_file': output_file,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем статистику
            stats_file = output_file.replace('.xlsx', '_stats.json').replace('.csv', '_stats.json').replace('.json', '_stats.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Обработка завершена. Статистика: {statistics}")
            self.update_progress("Обработка завершена!", len(queries), len(queries))
            
            return statistics
            
        except Exception as e:
            logger.error(f"Ошибка массового поиска: {e}")
            logger.error(traceback.format_exc())
            raise

# Функции для удобного использования
def load_queries_from_file(filepath: str) -> List[str]:
    """Загружает запросы из файла"""
    processor = BatchSearchProcessor()
    return processor.load_queries_from_file(filepath)

def export_results(results: List[Dict[str, Any]], filepath: str, format_type: str = 'auto'):
    """Экспортирует результаты в файл"""
    processor = BatchSearchProcessor()
    processor.export_results(results, filepath, format_type)

def batch_search_from_file(input_file: str, output_file: str, max_pages: int = 3, 
                          batch_size: int = 50, format_type: str = 'auto') -> Dict[str, Any]:
    """Основная функция массового поиска"""
    processor = BatchSearchProcessor()
    return processor.batch_search_from_file(input_file, output_file, max_pages, batch_size, format_type)

# Пример использования
if __name__ == "__main__":
    # Пример обработки файла
    try:
        input_file = "test_products.csv"
        output_file = "batch_results.xlsx"
        
        if os.path.exists(input_file):
            stats = batch_search_from_file(
                input_file=input_file,
                output_file=output_file,
                max_pages=1,
                batch_size=10,
                format_type='excel'
            )
            print(f"Обработка завершена: {stats}")
        else:
            print(f"Файл {input_file} не найден")
            
    except Exception as e:
        print(f"Ошибка: {e}") 