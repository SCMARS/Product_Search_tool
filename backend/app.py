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
from allegro import search_allegro
from amazon import search_amazon
from aliexpress import search_aliexpress

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True, allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

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
                allegro_results = search_allegro(product_name, limit=1)
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
    """
    Endpoint to upload and process a CSV file containing product names.

    The CSV file must have a 'product' column.
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
    """
    Endpoint to retrieve the results of CSV processing.

    Returns:
        JSON response containing the results from results.json
    """
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
