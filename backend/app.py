from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures
from allegro import search_allegro
from amazon import search_amazon
from aliexpress import search_aliexpress

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
