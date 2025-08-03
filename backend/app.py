from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures
import os
import requests
import base64
import io
import json
import time
import threading
import pandas as pd
from PIL import Image
from dotenv import load_dotenv

from allegro_enhanced import search_allegro_enhanced_sync as search_allegro
from amazon import search_amazon
from aliexpress import search_aliexpress, search_aliexpress_api


load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True, allow_headers=["Content-Type", "Authorization", "X-Requested-With"], methods=["GET", "POST", "OPTIONS", "DELETE"], expose_headers=["Content-Disposition"])

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Product Search API. Use /api/search endpoint to search for products."})

@app.route('/health')
def health_check():
    """Health check endpoint для Docker"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'services': {
            'flask': 'running',
            'playwright': 'available'
        }
    })

@app.route('/api/generate-product-description', methods=['POST'])
def generate_product_description():

    print("=== Product Description Generation Request ===")
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400


    product_name = data.get('name', '')
    product_price = data.get('price', '')
    product_url = data.get('url', '')
    product_image = data.get('image', '')
    source_platform = data.get('source', 'Unknown')

    if not product_name:
        return jsonify({'error': 'Product name is required'}), 400

    print(f"Generating description for: {product_name[:50]}...")
    print(f"Source: {source_platform}")
    print(f"Price: {product_price}")


    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        # Если API ключ не настроен, возвращаем базовое описание
        basic_description = f"""
📱 **{product_name}**

🔹 **Основные характеристики:**
• Высокое качество и надежность
• Современные технологии
• Отличное соотношение цена/качество

🔹 **Преимущества:**
• Проверенный производитель
• Гарантия качества
• Быстрая доставка

🔹 **Применение:**
Подходит для повседневного использования и профессиональных задач.

💡 **Рекомендация:** Для получения более детального AI-описания настройте OpenAI API ключ в файле .env

---
*Источник: {source_platform}*
*Цена: {product_price}*
        """.strip()
        
        return jsonify({
            'success': True,
            'description': basic_description,
            'product_info': {
                'name': product_name,
                'price': product_price,
                'source': source_platform
            },
            'note': 'Basic description generated. Set OPENAI_API_KEY for AI-powered descriptions.'
        })

    try:
        # Создаем промпт для генерации описания
        prompt = f"""
Создай профессиональное описание товара для интернет-магазина на основе следующей информации:

Название товара: {product_name}
Цена: {product_price}
Источник: {source_platform}

Требования к описанию:
1. Напиши привлекательное и информативное описание на русском языке
2. Выдели ключевые особенности и преимущества товара
3. Используй продающий стиль текста
4. Добавь информацию о качестве и надежности
5. Упомяни возможные варианты использования
6. Сделай описание длиной 150-300 слов
7. Используй эмодзи для привлекательности
8. Структурируй текст с абзацами
9. Опиши товар максимально точно, основываясь на его названии
10. Не добавляй информацию, которой нет в названии товара

ВАЖНО: Описание должно точно соответствовать названию товара. Если в названии указан конкретный товар (например, iPhone 15 Pro Max), то описание должно быть именно об этом товаре, а не о других моделях.

Создай описание, которое поможет покупателю принять решение о покупке.
"""

        # Отправляем запрос к OpenAI
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',  # Используем более экономичную модель
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Ты профессиональный копирайтер, специализирующийся на создании продающих описаний товаров для интернет-магазинов. Твоя задача - создавать привлекательные, информативные и убедительные описания, которые точно соответствуют названию товара и помогают покупателям принять решение о покупке.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 600,
                'temperature': 0.5
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        generated_description = result['choices'][0]['message']['content']

        print("✅ Description generated successfully")

        return jsonify({
            'success': True,
            'description': generated_description,
            'product_info': {
                'name': product_name,
                'price': product_price,
                'source': source_platform
            }
        })

    except requests.exceptions.RequestException as e:
        print(f"OpenAI API error: {e}")

        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_message = error_detail.get('error', {}).get('message', 'Unknown API error')

                if 'rate limit' in error_message.lower():
                    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
                elif 'invalid api key' in error_message.lower():
                    return jsonify({'error': 'Invalid OpenAI API key'}), 500
                else:
                    return jsonify({'error': f'OpenAI API error: {error_message}'}), 500

            except Exception as parse_error:
                return jsonify({'error': 'Could not process OpenAI API response'}), 500

        return jsonify({'error': f'Failed to generate description: {str(e)}'}), 500

    except Exception as e:
        print(f"Error generating description: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400

    query = data['query']

    # Запускаем поиск на всех платформах параллельно
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Включаем Allegro обратно
        allegro_future = executor.submit(search_allegro, query)
        amazon_future = executor.submit(search_amazon, query, limit=10)
        aliexpress_future = executor.submit(search_aliexpress, query, limit=10)

        # Получаем результаты
        allegro_results = allegro_future.result()
        amazon_results = amazon_future.result()
        aliexpress_results = aliexpress_future.result()

    # Дополнительная сортировка результатов по релевантности
    def sort_by_relevance(results):
        if not results:
            return results
        return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)

    # Сортируем результаты по релевантности
    allegro_results = sort_by_relevance(allegro_results)
    amazon_results = sort_by_relevance(amazon_results)
    aliexpress_results = sort_by_relevance(aliexpress_results)

    # Формируем ответ
    response_data = {
        'allegro': allegro_results,
        'amazon': amazon_results,
        'aliexpress': aliexpress_results
    }

    print(f"Total response: Allegro={len(allegro_results)}, Amazon={len(amazon_results)}, AliExpress={len(aliexpress_results)}")
    print("✅ Результаты отсортированы по релевантности")

    return jsonify(response_data)

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    print("=== Image Generation Request Received ===")
    data = request.get_json()
    if not data or 'description' not in data:
        print("Error: Missing description parameter")
        return jsonify({'error': 'Missing description parameter'}), 400

    description = data['description']
    print(f"Description: {description[:50]}..." if len(description) > 50 else f"Description: {description}")

    # Get OpenAI API key from environment variables
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("Error: OpenAI API key not configured")
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    print(f"Using OpenAI API key: {openai_api_key[:10]}...")

    # Создаем специальный промпт для генерации изображения на основе названия товара
    try:
        # Извлекаем название товара из описания - упрощенная логика
        product_name = description.strip()
        
        # Очищаем название от лишних символов
        product_name = product_name.replace('(Generalüberholt)', '').replace('(Refurbished)', '').strip()
        
        # Ограничиваем длину названия для промпта
        if len(product_name) > 100:
            product_name = product_name[:100]
        
        # М
        image_prompt = product_name

        print(f"Generated image prompt: {image_prompt}")

        # Call OpenAI API to generate image with DALL-E 3
        response = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'dall-e-3',  # Use the latest DALL-E model
                'prompt': image_prompt,
                'n': 1,
                'size': '1024x1024',  # Standard size for DALL-E 3
                'quality': 'standard',  # Can be 'standard' or 'hd'
                'response_format': 'url'
            },
            timeout=30  # 30 seconds timeout
        )

        # Check if the request was successful
        response.raise_for_status()

        # Extract image URL from response
        result = response.json()
        print(f"OpenAI API response status code: {response.status_code}")

        # Check if the response contains the expected data
        if 'data' not in result or not result['data'] or 'url' not in result['data'][0]:
            print(f"Unexpected API response format: {result}")
            return jsonify({'error': 'Unexpected response format from OpenAI API'}), 500

        image_url = result['data'][0]['url']
        print("Successfully generated image URL")

        return jsonify({'image_url': image_url})

    except requests.exceptions.RequestException as e:
        print(f"OpenAI API error: {e}")

        # Handle different types of request exceptions
        if isinstance(e, requests.exceptions.Timeout):
            print("Request timed out")
            return jsonify({'error': 'The request to OpenAI API timed out. Please try again later.'}), 504
        elif isinstance(e, requests.exceptions.ConnectionError):
            print("Connection error")
            return jsonify({'error': 'Could not connect to OpenAI API. Please check your internet connection.'}), 503
        elif hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            print(f"API response status code: {status_code}")

            try:
                error_detail = e.response.json()
                print(f"API response error: {error_detail}")
                error_message = error_detail.get('error', {}).get('message', 'Unknown API error')
                error_type = error_detail.get('error', {}).get('type', '')
                error_code = error_detail.get('error', {}).get('code', '')

                print(f"Error type: {error_type}, Error code: {error_code}")

                # Check for specific error types
                if 'too large' in error_message.lower() or 'size' in error_message.lower():
                    return jsonify({'error': 'The description is too large for processing. Please try a shorter description.'}), 400
                elif 'rate limit' in error_message.lower() or error_type == 'rate_limit_exceeded':
                    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
                elif 'invalid api key' in error_message.lower() or error_type == 'invalid_request_error' and 'api key' in error_message.lower():
                    return jsonify({'error': 'Invalid API key. Please check your configuration.'}), 500
                elif 'content policy' in error_message.lower() or error_type == 'content_policy_violation':
                    return jsonify({'error': 'The description violates content policy. Please modify your description.'}), 400
                elif 'billing' in error_message.lower() or 'account' in error_message.lower():
                    return jsonify({'error': 'OpenAI API billing or account issue. Please check your OpenAI account.'}), 402
                else:
                    return jsonify({'error': f'OpenAI API error: {error_message}'}), status_code

            except ValueError:
                return jsonify({'error': f'OpenAI API error with status code: {status_code}'}), status_code

        else:
            return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    # Check if image file is present in the request
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']

    # Check if the file is empty
    if image_file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400

    # Check if the file is an image
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in image_file.filename or \
       image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': 'File must be an image (PNG, JPG, JPEG, GIF)'}), 400

    # Get OpenAI API key from environment variables
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    # Validate the API key format
    if not ((openai_api_key.startswith('sk-') or openai_api_key.startswith('sk-proj-')) and len(openai_api_key) > 20):
        print(f"Warning: OpenAI API key may not be in the correct format: {openai_api_key[:10]}...")
        # Continue anyway as the format might be valid for certain account types

    try:
        # Read the image file
        image_data = image_file.read()

        # Check if the image is too large (10MB limit)
        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'error': 'Image is too large. Please upload an image smaller than 10MB.'}), 400

        # Resize the image to reduce its size
        try:
            img = Image.open(io.BytesIO(image_data))

            # Resize the image while maintaining aspect ratio
            max_size = (800, 800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert to RGB if the image is in RGBA mode (has transparency)
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Save the resized image to a bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            # Encode the resized image as base64
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Check if the base64 encoded image is too large for the API (max ~4MB)
            if len(base64_image) > 4 * 1024 * 1024:
                # Try with lower quality
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=50)
                buffer.seek(0)
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

                # If still too large, resize further
                if len(base64_image) > 4 * 1024 * 1024:
                    max_size = (400, 400)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=50)
                    buffer.seek(0)
                    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500

        # Call OpenAI API to analyze the image
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            timeout=30,  # Add a timeout to prevent hanging requests
            json={
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': [

                            {
                                'type': 'text',
                                'text': 'You are a product recognition system. '
                                        'Your only task is to return the exact product name shown in the image, '
                                        'as it would appear in a product catalog. '
                                        'Do not include any explanations, descriptions, or extra text. '
                                        'Only return the product title like "iPhone 16 Pro Max", "Sony WH-1000XM5", etc.'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{base64_image}',
                                    'detail': 'low'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 300,
                'temperature': 0.7
            }
        )

        # Check if the request was successful
        response.raise_for_status()

        # Extract the analysis from the response
        result = response.json()
        analysis = result['choices'][0]['message']['content']

        return jsonify({
            'analysis': analysis,
            'success': True
        })

    except requests.exceptions.RequestException as e:
        print(f"OpenAI API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"API response error: {error_detail}")
                error_message = error_detail.get('error', {}).get('message', 'Unknown API error')

                # Check for specific error types
                if 'too large' in error_message.lower() or 'size' in error_message.lower():
                    return jsonify({'error': 'The image is too large for processing. Please try a smaller image.'}), 400
                elif 'rate limit' in error_message.lower():
                    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
                elif 'invalid api key' in error_message.lower():
                    return jsonify({'error': 'Invalid API key. Please check your configuration.'}), 500
                else:
                    return jsonify({'error': f'OpenAI API error: {error_message}'}), 500
            except Exception as parse_error:
                print(f"Could not parse error response: {e.response.text}")
                print(f"Parse error: {parse_error}")
                return jsonify({'error': 'Could not process the API response. Please try again.'}), 500
        return jsonify({'error': f'Failed to analyze image: {str(e)}'}), 500
    except Exception as e:
        print(f"Error analyzing image: {e}")
        import traceback
        traceback.print_exc()

        # Provide more user-friendly error messages based on the exception
        if 'memory' in str(e).lower():
            return jsonify({'error': 'Server memory error while processing the image. Please try a smaller image.'}), 500
        elif 'timeout' in str(e).lower():
            return jsonify({'error': 'The request timed out. Please try again later.'}), 504
        else:
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

def process_csv(df):
    """
    Process a DataFrame containing product characteristics.
    For each product, search on Amazon, Allegro, and AliExpress using enhanced matching.
    Save results to results.json.

    Args:
        df (pandas.DataFrame): DataFrame with product characteristics
    """
    try:
        # Очищаем старые результаты для получения свежих данных
        if os.path.exists('backend/results.json'):
            os.remove('backend/results.json')
            print("🗑️ Удален старый файл результатов для получения свежих данных")

        # Пытаемся использовать улучшенный ProductMatcher
        from product_matcher import ProductMatcher

        # Создаем временный файл для обработки
        temp_file = 'temp_upload.csv'
        df.to_csv(temp_file, index=False, encoding='utf-8')

        # Используем ProductMatcher для обработки
        matcher = ProductMatcher()
        results = matcher.process_file(temp_file, 'backend/results.json')

        # Удаляем временный файл
        if os.path.exists(temp_file):
            os.remove(temp_file)

        print(f"Enhanced processing completed: {len(results)} products processed")

    except Exception as e:
        print(f"Error in enhanced processing: {e}")
        # Fallback to simple processing
        process_csv_simple(df)

def process_csv_simple(df):
    """
    Простая обработка CSV файла (fallback)
    """
    # Очищаем старые результаты
    if os.path.exists('backend/results.json'):
        os.remove('backend/results.json')
        print("🗑️ Удален старый файл результатов (fallback)")

    results = []

    # Determine which column to use for product names
    product_column = None
    for col in ['product', 'product_name', 'название', 'name']:
        if col in df.columns:
            product_column = col
            break

    if not product_column:
        print("Не найдена колонка с названием товара")
        return

    for index, row in df.iterrows():
        product_name = row[product_column]
        if pd.isna(product_name) or str(product_name).strip() == '':
            continue

        product_result = {"product": str(product_name), "row_index": index + 1}

        try:
            # Search Amazon
            try:
                amazon_results = search_amazon(str(product_name), max_pages=1)
                product_result["amazon"] = amazon_results[:5]  # Limit to 5 results
                print(f"Amazon: found {len(amazon_results)} products for {product_name}")
            except Exception as e:
                product_result["amazon_error"] = str(e)
                print(f"Error searching Amazon for {product_name}: {e}")

            # Search Allegro
            try:
                allegro_results = search_allegro(str(product_name))
                product_result["allegro"] = allegro_results[:5]  # Limit to 5 results
                print(f"Allegro: found {len(allegro_results)} products for {product_name}")
            except Exception as e:
                product_result["allegro_error"] = str(e)
                print(f"Error searching Allegro for {product_name}: {e}")

            # Search AliExpress
            try:
                aliexpress_results = search_aliexpress(str(product_name), limit=5)
                product_result["aliexpress"] = aliexpress_results
                print(f"AliExpress: found {len(aliexpress_results)} products for {product_name}")
            except Exception as e:
                product_result["aliexpress_error"] = str(e)
                print(f"Error searching AliExpress for {product_name}: {e}")

        except Exception as e:
            product_result["error"] = f"Error processing product: {str(e)}"
            print(f"Error processing product {product_name}: {e}")

        results.append(product_result)

        # Sleep to avoid rate limiting
        time.sleep(1)

    # Save results to backend/results.json
    try:
        with open('backend/results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to backend/results.json ({len(results)} products processed)")
    except Exception as e:
        print(f"Error saving results to file: {e}")

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """
    Endpoint to upload and process a CSV or Excel file containing product characteristics.

    The file can contain various columns like:
    - product, product_name, название, name (for product names)
    - brand, бренд, марка (for brands)
    - category, категория (for categories)
    - color, цвет (for colors)
    - size, размер (for sizes)
    - keywords, ключевые_слова (for additional keywords)

    Processing is done in a background thread.

    Returns:
        JSON response indicating success or error
    """
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check if the file is empty
    if file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400

    # Check if the file is CSV or Excel
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return jsonify({'error': 'File must be CSV (.csv) or Excel (.xlsx, .xls)'}), 400

    try:
        # Read the file based on extension
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8')
        else:
            df = pd.read_excel(file)

        # Check if we have at least one column that could contain product information
        product_columns = ['product', 'product_name', 'название', 'name', 'brand', 'бренд']
        has_product_info = any(col in df.columns for col in product_columns)

        if not has_product_info:
            return jsonify({
                'error': 'File must contain at least one of these columns: product, product_name, название, name, brand, бренд'
            }), 400

        # Log available columns for debugging
        print(f"Available columns: {list(df.columns)}")
        print(f"Processing {len(df)} rows")

        # Start background processing
        thread = threading.Thread(target=process_csv, args=(df,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'Processing {len(df)} products in the background',
            'products_count': len(df),
            'columns': list(df.columns)
        })

    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 500

@app.route('/api/csv-results', methods=['GET'])
def get_csv_results():
    """
    Endpoint to retrieve the results of CSV processing.

    Returns:
        JSON response containing the results from results.json
    """
    try:
        # Check if results.json exists
        if not os.path.exists('backend/results.json'):
            return jsonify({
                'success': False,
                'message': 'No results available. Please upload a CSV file first.'
            }), 404

        # Read the results.json file
        with open('backend/results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving results: {str(e)}'
        }), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all files in the uploads directory"""
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        files = []
        for filename in os.listdir(uploads_dir):
            if filename.endswith(('.csv', '.xlsx', '.json')):
                filepath = os.path.join(uploads_dir, filename)
                file_stats = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': file_stats.st_size,
                    'modified': time.ctime(file_stats.st_mtime),
                    'type': filename.split('.')[-1].upper()
                })

        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific file"""
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        filepath = os.path.join(uploads_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({
                'success': True,
                'message': f'File {filename} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/<filename>/download', methods=['GET'])
def download_file(filename):
    """Download a specific file"""
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        filepath = os.path.join(uploads_dir, filename)

        if os.path.exists(filepath):
            from flask import send_file
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-image-prompt', methods=['POST'])
def generate_image_prompt():
    data = request.get_json()
    if not data or 'product_name' not in data:
        return jsonify({'error': 'Missing product_name parameter'}), 400

    product_name = data['product_name']
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    # Составляем промпт для GPT
    gpt_prompt = (
        f"Ты — эксперт по генерации промптов для нейросети DALL-E. "
        f"Твоя задача — создать короткий, но максимально точный промпт для генерации реалистичного изображения товара по его названию. "
        f"Пиши только на английском языке. Не добавляй лишних деталей, только то, что явно указано в названии. "
        f"Если в названии есть цвет или модель — обязательно укажи это. Не добавляй слова вроде 'professional', 'photo', 'white background', 'no watermark', 'e-commerce' и т.д. Просто опиши товар максимально кратко и точно для DALL-E.\n"
        f"Название товара: {product_name}\n"
        f"Промпт для DALL-E:"
    )

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a prompt engineer for DALL-E.'},
                    {'role': 'user', 'content': gpt_prompt}
                ],
                'max_tokens': 100,
                'temperature': 0.2
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        prompt = result['choices'][0]['message']['content'].strip()
        return jsonify({'prompt': prompt})
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        return jsonify({'error': 'Failed to generate image prompt'}), 500

if __name__ == '__main__':
    # Определяем режим запуска
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    host = '0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1'
    app.run(debug=debug_mode, host=host, port=5001)
