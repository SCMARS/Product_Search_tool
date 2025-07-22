import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Allegro API credentials
CLIENT_ID = os.getenv('ALLEGRO_CLIENT_ID')
CLIENT_SECRET = os.getenv('ALLEGRO_CLIENT_SECRET')

# Allegro API endpoints
AUTH_URL = 'https://allegro.pl/auth/oauth/token'
SEARCH_URL = 'https://api.allegro.pl/offers/listing'

def get_access_token():
    """Get OAuth access token from Allegro API"""
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(AUTH_URL, auth=auth, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Error getting access token: {response.status_code}")
        print(response.text)
        return None

def search_allegro(query, limit=3):
    """Search for products on Allegro"""
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return []
    
    # Set up request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json'
    }
    
    params = {
        'phrase': query,
        'limit': limit,
        'sort': '-relevance'
    }
    
    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get('items', {}).get('regular', [])[:limit]:
                offer = item.get('offer', {})
                
                # Extract product details
                name = offer.get('name', 'No name')
                price_data = offer.get('sellingMode', {}).get('price', {})
                price = f"{price_data.get('amount', '0')} {price_data.get('currency', 'PLN')}"
                
                # Get image URL
                images = offer.get('images', [])
                image_url = images[0].get('url') if images else ''
                
                # Get product URL
                product_url = offer.get('url', '')
                
                results.append({
                    'name': name,
                    'price': price,
                    'image': image_url,
                    'url': product_url
                })
            
            return results
        else:
            print(f"Error searching Allegro: {response.status_code}")
            print(response.text)
            return []
    
    except Exception as e:
        print(f"Exception during Allegro search: {str(e)}")
        return []

# For testing
if __name__ == "__main__":
    test_query = "iphone 13"
    results = search_allegro(test_query)
    print(f"Found {len(results)} results for '{test_query}':")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']} - {result['price']}")
        print(f"   Image: {result['image']}")
        print(f"   URL: {result['url']}")
        print()