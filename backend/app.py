from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures
import os
import requests
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
    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({'error': 'Missing description parameter'}), 400

    description = data['description']

    # Get OpenAI API key from environment variables
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    try:
        # Call OpenAI API to generate image
        response = requests.post(
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
            }
        )

        # Check if the request was successful
        response.raise_for_status()

        # Extract image URL from response
        result = response.json()
        image_url = result['data'][0]['url']

        return jsonify({'image_url': image_url})

    except requests.exceptions.RequestException as e:
        print(f"OpenAI API error: {e}")
        return jsonify({'error': 'Failed to generate image. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
