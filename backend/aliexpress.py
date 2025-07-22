import requests
import os

def search_aliexpress(query, limit=3):
    """Search for products on AliExpress using RapidAPI"""
    results = []

    try:
        # RapidAPI endpoint for AliExpress
        url = "https://aliexpress-datahub.p.rapidapi.com/products/search"

        # Query parameters
        querystring = {
            "keywords": query,
            "page": "1",
            "sort": "best_match"
        }

        # Headers with RapidAPI key and host
        # In a production environment, you should store the API key in environment variables
        headers = {
            "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY_HERE"),
            "X-RapidAPI-Host": "aliexpress-datahub.p.rapidapi.com"
        }

        # Make the API request
        response = requests.get(url, headers=headers, params=querystring)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()

            # Extract product information from the response
            # The exact structure depends on the API response format
            products = data.get("items", [])

            # Process only the first 'limit' number of products
            for product in products[:limit]:
                try:
                    # Extract product details based on the API response structure
                    name = product.get("title", "No name")

                    # Format price
                    price_data = product.get("price", {})
                    price = f"US ${price_data.get('value', 'N/A')}" if price_data else "Price not available"

                    # Get image URL
                    image_url = product.get("image", {}).get("imgUrl", "")

                    # Get product URL
                    product_url = product.get("productUrl", "")
                    if product_url and not product_url.startswith("http"):
                        product_url = f"https:{product_url}"

                    # Get description - use name as default
                    description = name

                    # Try to get a better description from the API response
                    if "description" in product:
                        api_description = product.get("description", "")
                        if api_description:
                            description = api_description

                    # Add to results
                    results.append({
                        "name": name,
                        "price": price,
                        "image": image_url,
                        "url": product_url,
                        "description": description
                    })

                except Exception as e:
                    print(f"Error processing AliExpress product: {str(e)}")
                    continue
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Exception during AliExpress API search: {str(e)}")

    return results

# For testing
if __name__ == "__main__":
    test_query = "iphone 13"
    results = search_aliexpress(test_query)
    print(f"Found {len(results)} results for '{test_query}':")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']} - {result['price']}")
        print(f"   Image: {result['image']}")
        print(f"   URL: {result['url']}")
        print()
