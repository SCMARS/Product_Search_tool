import sys
from amazon import search_amazon

def test_amazon_search():
    query = "iphone 13"
    print(f"Searching for '{query}'...")

    # Add more debugging
    print("Starting search...")
    results = search_amazon(query, limit=2)
    print(f"Search completed. Results type: {type(results)}, length: {len(results) if results else 0}")

    if not results:
        print("No results returned. Check the search function.")
        return False

    print(f"Found {len(results)} results:")
    for i, product in enumerate(results, 1):
        print(f"\n{i}. {product['name']}")
        print(f"Price: {product['price']}")
        print(f"URL: {product['url']}")
        print(f"Image: {product['image']}")
        print("Description:")
        print(product.get('description', 'No description available'))

    return len(results) > 0

if __name__ == "__main__":
    try:
        success = test_amazon_search()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
