
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
from allegro import search_allegro_improved as search_allegro
from amazon import search_amazon
from aliexpress import search_aliexpress
from batch_search import BatchSearchProcessor


load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True, allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])


batch_processor = None
current_batch_status = {
    'is_running': False,
    'progress': 0,
    'message': '',
    'total': 0,
    'current': 0,
    'failed': 0
}

def progress_callback(progress_data):
    """Callback для обновления прогресса"""
    global current_batch_status
    current_batch_status.update(progress_data)
    current_batch_status['is_running'] = True

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Product Search API. Use /api/search endpoint to search for products."})

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400

    query = data['query']

    with concurrent.futures.ThreadPoolExecutor() as executor:
        allegro_future = executor.submit(search_allegro, query)
        amazon_future = executor.submit(search_amazon, query)
        aliexpress_future = executor.submit(search_aliexpress, query)

        try:
            allegro_results = allegro_future.result()
        except Exception as e:
            print(f"Allegro search error: {e}")
            allegro_results = []

        try:
            amazon_results = amazon_future.result()
        except Exception as e:
            print(f"Amazon search error: {e}")
            amazon_results = []

        try:
            aliexpress_results = aliexpress_future.result()
        except Exception as e:
            print(f"Aliexpress search error: {e}")
            aliexpress_results = []

    return jsonify({
        'allegro': allegro_results,
        'amazon': amazon_results,
        'aliexpress': aliexpress_results
    })

@app.route("/api/aliexpress", methods=["GET"])
def aliexpress_route():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    results = search_aliexpress(query)
    return jsonify(results)

@app.route('/api/batch-search', methods=['POST'])
def batch_search():
    """
    Новый эндпоинт для массовой обработки
    """
    global batch_processor, current_batch_status
    
    if current_batch_status['is_running']:
        return jsonify({
            'error': 'Batch processing is already running. Please wait for completion.'
        }), 409
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400

    # Проверяем поддерживаемые форматы
    supported_formats = ['.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in supported_formats:
        return jsonify({'error': f'Unsupported file format. Supported: {", ".join(supported_formats)}'}), 400

    try:
        # Сохраняем файл временно
        temp_input_file = f"temp_input_{int(time.time())}{file_ext}"
        file.save(temp_input_file)
        
        # Получаем параметры из запроса
        output_format = request.form.get('output_format', 'excel')
        batch_size = int(request.form.get('batch_size', 50))
        max_pages = int(request.form.get('max_pages', 1))
        
        # Определяем выходной файл
        output_ext = '.xlsx' if output_format == 'excel' else '.csv' if output_format == 'csv' else '.json'
        output_file = f"batch_results_{int(time.time())}{output_ext}"
        
        # Сбрасываем статус
        current_batch_status = {
            'is_running': True,
            'progress': 0,
            'message': 'Starting batch processing...',
            'total': 0,
            'current': 0,
            'failed': 0
        }
        
        # Создаем процессор
        batch_processor = BatchSearchProcessor(max_workers=10)
        batch_processor.set_progress_callback(progress_callback)
        
        # Запускаем обработку в отдельном потоке
        def run_batch_processing():
            global current_batch_status
            try:
                batch_processor.batch_search_from_file(
                    input_file=temp_input_file,
                    output_file=output_file,
                    max_pages=max_pages,
                    batch_size=batch_size,
                    format_type=output_format
                )
                current_batch_status['is_running'] = False
                current_batch_status['message'] = 'Processing completed successfully!'
                current_batch_status['progress'] = 100
                
                # Удаляем временный файл
                if os.path.exists(temp_input_file):
                    os.remove(temp_input_file)
                    
            except Exception as e:
                current_batch_status['is_running'] = False
                current_batch_status['message'] = f'Error: {str(e)}'
                # logger.error(f"Batch processing error: {e}") # logger is not defined
                
                # Удаляем временный файл
                if os.path.exists(temp_input_file):
                    os.remove(temp_input_file)
        
        thread = threading.Thread(target=run_batch_processing)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Batch processing started',
            'output_file': output_file,
            'job_id': int(time.time())
        })
        
    except Exception as e:
        # logger.error(f"Error starting batch processing: {e}") # logger is not defined
        return jsonify({'error': f'Error starting batch processing: {str(e)}'}), 500

@app.route('/api/batch-status', methods=['GET'])
def batch_status():
    """
    Получение статуса массовой обработки
    """
    global current_batch_status
    
    return jsonify({
        'success': True,
        'status': current_batch_status
    })

@app.route('/api/batch-results/<filename>', methods=['GET'])
def get_batch_results(filename):
    """
    Получение результатов массовой обработки
    """
    try:
        file_path = filename
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'Results file not found'
            }), 404
        
        # Определяем тип файла
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            return jsonify({
                'success': True,
                'results': results,
                'filename': filename
            })
        else:
            # Для Excel/CSV возвращаем ссылку на скачивание
            return jsonify({
                'success': True,
                'download_url': f'/api/download/{filename}',
                'filename': filename
            })
            
    except Exception as e:
        # logger.error(f"Error retrieving batch results: {e}") # logger is not defined
        return jsonify({
            'success': False,
            'message': f'Error retrieving results: {str(e)}'
        }), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Скачивание файла с результатами
    """
    try:
        file_path = filename
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        # logger.error(f"Error downloading file: {e}") # logger is not defined
        return jsonify({
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }), 500


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

    # Validate the API key format
    if not ((openai_api_key.startswith('sk-') or openai_api_key.startswith('sk-proj-')) and len(openai_api_key) > 20):
        print(f"Warning: OpenAI API key may not be in the correct format: {openai_api_key[:10]}...")
        # Continue anyway as the format might be valid for certain account types

    # First try with DALL-E 3, then fall back to DALL-E 2 if needed
    try:
        print("Sending request to OpenAI API using DALL-E 3...")
        # Call OpenAI API to generate image with DALL-E 3
        response = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'dall-e-3',  # Use the latest DALL-E model
                'prompt': description,
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
                elif 'model' in error_message.lower() or ('parameter' in error_message.lower() and 'model' in error_message.lower()):
                    # Try fallback without specifying model (use API default)
                    print("Model parameter issue, trying fallback without specifying model...")
                    try:
                        fallback_response = requests.post(
                            'https://api.openai.com/v1/images/generations',
                            headers={
                                'Authorization': f'Bearer {openai_api_key}',
                                'Content-Type': 'application/json'
                            },
                            json={
                                'prompt': description,
                                'n': 1,
                                'size': '512x512',
                                'response_format': 'url'
                            },
                            timeout=30  # 30 seconds timeout
                        )

                        # Check if the fallback request was successful
                        fallback_response.raise_for_status()

                        # Extract image URL from fallback response
                        fallback_result = fallback_response.json()
                        print(f"Default model fallback response status code: {fallback_response.status_code}")

                        # Check if the fallback response contains the expected data
                        if 'data' not in fallback_result or not fallback_result['data'] or 'url' not in fallback_result['data'][0]:
                            print(f"Unexpected API fallback response format: {fallback_result}")
                            return jsonify({'error': 'Unexpected response format from OpenAI API'}), 500

                        fallback_image_url = fallback_result['data'][0]['url']
                        print("Successfully generated image URL using default model fallback")

                        return jsonify({'image_url': fallback_image_url})
                    except Exception as fallback_error:
                        print(f"Default model fallback also failed: {fallback_error}")
                        return jsonify({'error': f'OpenAI API model error: {error_message}'}), 500
                elif status_code == 401:
                    return jsonify({'error': 'Authentication error with OpenAI API. Please check your API key.'}), 401
                elif status_code == 403:
                    # Try fallback to DALL-E 2 if DALL-E 3 is not available
                    print("DALL-E 3 not available, trying DALL-E 2 as fallback...")
                    try:
                        fallback_response = requests.post(
                            'https://api.openai.com/v1/images/generations',
                            headers={
                                'Authorization': f'Bearer {openai_api_key}',
                                'Content-Type': 'application/json'
                            },
                            json={
                                'model': 'dall-e-2',  # Fallback to DALL-E 2
                                'prompt': description,
                                'n': 1,
                                'size': '512x512',  # Standard size for DALL-E 2
                                'response_format': 'url'
                            },
                            timeout=30  # 30 seconds timeout
                        )

                        # Check if the fallback request was successful
                        fallback_response.raise_for_status()

                        # Extract image URL from fallback response
                        fallback_result = fallback_response.json()
                        print(f"DALL-E 2 fallback response status code: {fallback_response.status_code}")

                        # Check if the fallback response contains the expected data
                        if 'data' not in fallback_result or not fallback_result['data'] or 'url' not in fallback_result['data'][0]:
                            print(f"Unexpected API fallback response format: {fallback_result}")
                            return jsonify({'error': 'Unexpected response format from OpenAI API'}), 500

                        fallback_image_url = fallback_result['data'][0]['url']
                        print("Successfully generated image URL using DALL-E 2 fallback")

                        return jsonify({'image_url': fallback_image_url})
                    except Exception as fallback_error:
                        print(f"DALL-E 2 fallback also failed: {fallback_error}")
                        return jsonify({'error': 'Permission denied by OpenAI API. Your account may not have access to image generation.'}), 403
                else:
                    return jsonify({'error': f'OpenAI API error: {error_message}'}), 500
            except Exception as parse_error:
                print(f"Could not parse error response: {e.response.text}")
                print(f"Parse error: {parse_error}")
                return jsonify({'error': f'Could not process the API response (Status: {status_code}). Please try again.'}), 500

        # If there's no response object or other specific error info
        print("No response object or other specific error info")
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500
    except Exception as e:
        print(f"Error generating image: {e}")
        import traceback
        traceback.print_exc()

        # Provide more user-friendly error messages based on the exception
        if 'memory' in str(e).lower():
            return jsonify({'error': 'Server memory error while processing the request. Please try again later.'}), 500
        elif 'timeout' in str(e).lower():
            return jsonify({'error': 'The request timed out. Please try again later.'}), 504
        else:
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

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
    Process a DataFrame containing product names.
    For each product, search on Amazon, Allegro, and AliExpress.
    Save results to results.json.

    Args:
        df (pandas.DataFrame): DataFrame with a 'product' column
    """
    results = []

    for index, row in df.iterrows():
        product_name = row['product']
        product_result = {"product": product_name}

        try:
            # Search Amazon
            try:
                amazon_results = search_amazon(product_name, limit=1)
                if amazon_results:
                    product_result["amazon"] = {
                        "name": amazon_results[0]["name"],
                        "price": amazon_results[0]["price"],
                        "url": amazon_results[0]["url"]
                    }
            except Exception as e:
                product_result["error"] = f"Timeout while fetching amazon: {str(e)}"
                print(f"Error searching Amazon for {product_name}: {e}")

            # Search Allegro
            try:
                allegro_results = search_allegro(product_name, max_pages=1)
                if allegro_results:
                    product_result["allegro"] = {
                        "name": allegro_results[0]["name"],
                        "price": allegro_results[0]["price"],
                        "url": allegro_results[0]["url"]
                    }
            except Exception as e:
                if "error" not in product_result:
                    product_result["error"] = f"Timeout while fetching allegro: {str(e)}"
                print(f"Error searching Allegro for {product_name}: {e}")

            # Search AliExpress
            try:
                aliexpress_results = search_aliexpress(product_name, limit=1)
                if aliexpress_results:
                    product_result["aliexpress"] = {
                        "name": aliexpress_results[0]["name"],
                        "price": aliexpress_results[0]["price"],
                        "url": aliexpress_results[0]["url"]
                    }
            except Exception as e:
                if "error" not in product_result:
                    product_result["error"] = f"Timeout while fetching aliexpress: {str(e)}"
                print(f"Error searching AliExpress for {product_name}: {e}")

        except Exception as e:
            product_result["error"] = f"Error processing product: {str(e)}"
            print(f"Error processing product {product_name}: {e}")

        results.append(product_result)

        # Sleep to avoid rate limiting
        time.sleep(0.5)

    # Save results to results.json
    try:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to results.json ({len(results)} products processed)")
    except Exception as e:
        print(f"Error saving results to file: {e}")

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check if the file is empty
    if file.filename == '':
        return jsonify({'error': 'Empty file provided'}), 400

    # Check if the file is a CSV
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read the CSV file
        df = pd.read_csv(file)

        # Check if either 'product' or 'product_name' column exists
        if 'product' not in df.columns and 'product_name' not in df.columns:
            return jsonify({'error': 'CSV file must contain either a "product" or "product_name" column'}), 400

        # If only product_name exists, rename it to product for consistency
        if 'product_name' in df.columns and 'product' not in df.columns:
            df = df.rename(columns={'product_name': 'product'})

        # Start background processing
        thread = threading.Thread(target=process_csv, args=(df,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'Processing {len(df)} products in the background',
            'products_count': len(df)
        })

    except Exception as e:
        return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 500

@app.route('/api/csv-results', methods=['GET'])
def get_csv_results():

    try:
        # Check if results.json exists
        if not os.path.exists('results.json'):
            return jsonify({
                'success': False,
                'message': 'No results available. Please upload a CSV file first.'
            }), 404

        # Read the results.json file
        with open('results.json', 'r', encoding='utf-8') as f:
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

@app.route('/api/generate-allegro-listing', methods=['POST'])
def generate_allegro_listing():
    """
    Генерирует шаблон объявления для Allegro на основе данных товара
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Импортируем функции из allegro.py
        from allegro import create_full_allegro_listing, generate_allegro_listing_template
        
        # Проверяем, есть ли данные товара
        if 'product_data' not in data:
            return jsonify({'error': 'Missing product_data'}), 400
        
        product_data = data['product_data']
        
        # Проверяем обязательные поля
        required_fields = ['name', 'price']
        for field in required_fields:
            if field not in product_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Проверяем, использовать ли OpenAI
        use_openai = data.get('use_openai', False)
        
        # Генерируем шаблон объявления
        if data.get('full_template', False):
            # Полный шаблон с дополнительной информацией
            template = create_full_allegro_listing(product_data, use_openai)
        else:
            # Базовый шаблон
            template = generate_allegro_listing_template(product_data, use_openai)
        
        return jsonify({
            'success': True,
            'template': template,
            'message': f'Allegro listing template generated successfully{" with OpenAI" if use_openai else ""}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating Allegro listing template: {str(e)}'
        }), 500

@app.route('/api/generate-allegro-listing-from-search', methods=['POST'])
def generate_allegro_listing_from_search():
    """
    Генерирует шаблон объявления для Allegro на основе поискового запроса
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        query = data['query']
        
        # Импортируем функции
        from allegro import search_allegro_improved, create_full_allegro_listing, generate_allegro_listing_template
        
        # Ищем товары на Allegro
        allegro_results = search_allegro_improved(query, max_pages=1)
        
        if not allegro_results:
            return jsonify({
                'success': False,
                'error': 'No products found for the given query'
            }), 404
        
        # Берем первый найденный товар
        product_data = allegro_results[0]
        
        # Проверяем, использовать ли OpenAI
        use_openai = data.get('use_openai', False)
        
        # Генерируем шаблон объявления
        if data.get('full_template', False):
            template = create_full_allegro_listing(product_data, use_openai)
        else:
            template = generate_allegro_listing_template(product_data, use_openai)
        
        return jsonify({
            'success': True,
            'template': template,
            'source_product': product_data,
            'message': f'Allegro listing template generated for query: {query}{" with OpenAI" if use_openai else ""}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating Allegro listing template from search: {str(e)}'
        }), 500

@app.route('/api/generate-allegro-listing-batch', methods=['POST'])
def generate_allegro_listing_batch():
    """
    Генерирует шаблоны объявлений для Allegro для списка товаров
    """
    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'error': 'Missing products list'}), 400
        
        products = data['products']
        if not isinstance(products, list):
            return jsonify({'error': 'Products must be a list'}), 400
        
        # Импортируем функции
        from allegro import create_full_allegro_listing, generate_allegro_listing_template
        
        # Проверяем, использовать ли OpenAI
        use_openai = data.get('use_openai', False)
        
        templates = []
        
        for i, product in enumerate(products):
            try:
                if data.get('full_template', False):
                    template = create_full_allegro_listing(product, use_openai)
                else:
                    template = generate_allegro_listing_template(product, use_openai)
                
                templates.append({
                    'index': i,
                    'product_name': product.get('name', 'Unknown'),
                    'template': template,
                    'success': True
                })
                
            except Exception as e:
                templates.append({
                    'index': i,
                    'product_name': product.get('name', 'Unknown'),
                    'error': str(e),
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'templates': templates,
            'total_processed': len(products),
            'successful': len([t for t in templates if t['success']]),
            'failed': len([t for t in templates if not t['success']]),
            'message': f'Generated {len(templates)} Allegro listing templates{" with OpenAI" if use_openai else ""}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating batch Allegro listing templates: {str(e)}'
        }), 500

@app.route('/api/generate-allegro-listing-from-csv', methods=['POST'])
def generate_allegro_listing_from_csv():
    """
    Генерирует шаблоны объявлений для Allegro из CSV файла
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if the file is empty
        if file.filename == '':
            return jsonify({'error': 'Empty file provided'}), 400

        # Check if the file is a CSV
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400

        # Получаем параметры из формы
        use_openai = request.form.get('use_openai', 'false').lower() == 'true'
        full_template = request.form.get('full_template', 'false').lower() == 'true'
        search_products = request.form.get('search_products', 'false').lower() == 'true'

        try:
            # Read the CSV file
            df = pd.read_csv(file)

            # Check if either 'product' or 'product_name' column exists
            if 'product' not in df.columns and 'product_name' not in df.columns:
                return jsonify({'error': 'CSV file must contain either a "product" or "product_name" column'}), 400

            # If only product_name exists, rename it to product for consistency
            if 'product_name' in df.columns and 'product' not in df.columns:
                df = df.rename(columns={'product_name': 'product'})

            # Импортируем функции
            from allegro import create_full_allegro_listing, generate_allegro_listing_template, search_allegro_improved

            templates = []
            products_processed = 0

            for index, row in df.iterrows():
                try:
                    product_name = row['product']
                    
                    if search_products:
                        # Ищем товар на Allegro
                        allegro_results = search_allegro_improved(product_name, max_pages=1)
                        if allegro_results:
                            product_data = allegro_results[0]
                        else:
                            # Создаем базовые данные если товар не найден
                            product_data = {
                                'name': product_name,
                                'price': 'Cena do uzgodnienia',
                                'url': '',
                                'image': '',
                                'description': f'Produkt: {product_name}'
                            }
                    else:
                        # Используем только название товара
                        product_data = {
                            'name': product_name,
                            'price': 'Cena do uzgodnienia',
                            'url': '',
                            'image': '',
                            'description': f'Produkt: {product_name}'
                        }

                    # Генерируем шаблон объявления
                    if full_template:
                        template = create_full_allegro_listing(product_data, use_openai)
                    else:
                        template = generate_allegro_listing_template(product_data, use_openai)

                    templates.append({
                        'index': index,
                        'product_name': product_name,
                        'template': template,
                        'success': True
                    })

                    products_processed += 1

                except Exception as e:
                    templates.append({
                        'index': index,
                        'product_name': row.get('product', 'Unknown'),
                        'error': str(e),
                        'success': False
                    })

            # Сохраняем результаты в файл
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"allegro_templates_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'use_openai': use_openai,
                    'full_template': full_template,
                    'search_products': search_products,
                    'total_products': len(df),
                    'successful': len([t for t in templates if t['success']]),
                    'failed': len([t for t in templates if not t['success']]),
                    'templates': templates
                }, f, ensure_ascii=False, indent=2)

            return jsonify({
                'success': True,
                'templates': templates,
                'total_products': len(df),
                'successful': len([t for t in templates if t['success']]),
                'failed': len([t for t in templates if not t['success']]),
                'filename': filename,
                'message': f'Generated {len(templates)} Allegro listing templates from CSV{" with OpenAI" if use_openai else ""}'
            })

        except Exception as e:
            return jsonify({'error': f'Error processing CSV file: {str(e)}'}), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating Allegro listing templates from CSV: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
