from playwright.sync_api import sync_playwright
import time
import re
from difflib import SequenceMatcher

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def calculate_relevance_score(product_name, query):
    """Calculate detailed relevance score for a product"""
    query_lower = query.lower()
    product_lower = product_name.lower()
    query_words = query_lower.split()
    product_words = product_lower.split()

    scores = {
        'exact_match': 0,
        'word_order': 0,
        'word_coverage': 0,
        'brand_match': 0,
        'phrase_match': 0,
        'overall_similarity': 0
    }

    # Exact match bonus
    if query_lower in product_lower:
        scores['exact_match'] = 100

    # Word order preservation (consecutive words get bonus)
    consecutive_matches = 0
    max_consecutive = 0
    for i in range(len(query_words)):
        for j in range(len(product_words)):
            if query_words[i] == product_words[j]:
                consecutive = 1
                k, l = i + 1, j + 1
                while k < len(query_words) and l < len(product_words) and query_words[k] == product_words[l]:
                    consecutive += 1
                    k += 1
                    l += 1
                max_consecutive = max(max_consecutive, consecutive)
    scores['word_order'] = (max_consecutive / len(query_words)) * 50

    # Word coverage (how many query words are found)
    found_words = sum(1 for word in query_words if word in product_words)
    scores['word_coverage'] = (found_words / len(query_words)) * 30

    # Brand matching (first word is often brand)
    if len(query_words) > 0 and len(product_words) > 0:
        if query_words[0] in product_words[:3]:  # Brand usually in first 3 words
            scores['brand_match'] = 20

    # Phrase matching (2+ consecutive words)
    for i in range(len(query_words) - 1):
        phrase = f"{query_words[i]} {query_words[i+1]}"
        if phrase in product_lower:
            scores['phrase_match'] += 15

    # Overall similarity
    scores['overall_similarity'] = similarity(product_name, query) * 20

    return sum(scores.values()), scores

def matches_query(product_name, query, min_score=25):
    """Check if product name matches the search query with improved logic"""
    score, details = calculate_relevance_score(product_name, query)

    # Special rules for different types of queries
    query_lower = query.lower()
    product_lower = product_name.lower()
    query_words = set(query_lower.split())

    # Must have at least one main keyword
    essential_words = query_words - {'the', 'a', 'an', 'for', 'with', 'and', 'or'}
    if not essential_words:
        essential_words = query_words

    found_essential = sum(1 for word in essential_words if word in product_lower)

    # For brand + product queries (like "apple mouse"), both should be present
    if len(essential_words) >= 2:
        # If it's a brand + product query, require higher coverage
        required_coverage = 0.7 if len(essential_words) <= 3 else 0.6
        coverage_ratio = found_essential / len(essential_words)

        if coverage_ratio < required_coverage:
            return False

    # Minimum score threshold
    return score >= min_score

def search_amazon(query, limit=3, max_pages=3):
    results = []
    found_count = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            for page_num in range(1, max_pages + 1):
                if found_count >= limit:
                    break

                # Construct URL with page parameter
                if page_num == 1:
                    url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}"
                else:
                    url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}&page={page_num}"

                print(f"Searching page {page_num}...")
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(3)

                # Scroll down to load all content
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(2)

                # Get all product containers
                products = page.query_selector_all("div[data-asin][data-component-type='s-search-result']")
                valid_products = [p for p in products if p.get_attribute("data-asin") and p.get_attribute("data-asin") != ""]

                print(f"Found {len(valid_products)} products on page {page_num}")

                for product in valid_products:
                    if found_count >= limit:
                        break

                    asin = product.get_attribute("data-asin")

                    # Try multiple selectors for title
                    title_elem = product.query_selector("h2 a span")
                    if not title_elem:
                        title_elem = product.query_selector("h2 span")
                    if not title_elem:
                        title_elem = product.query_selector("h2 a")
                    if not title_elem:
                        continue

                    name = title_elem.inner_text().strip()

                    # Check if this product matches our query
                    relevance_score, score_details = calculate_relevance_score(name, query)
                    if not matches_query(name, query):
                        print(f"Skipping non-matching product: {name[:50]}... (Score: {relevance_score:.1f})")
                        continue

                    print(f"Found matching product: {name[:50]}... (Score: {relevance_score:.1f})")

                    # Get price
                    price_elem = product.query_selector("span.a-price span.a-offscreen")
                    if not price_elem:
                        price_elem = product.query_selector("span.a-price-whole")
                    price = price_elem.inner_text().strip() if price_elem else "Price not available"

                    # Get image
                    img_elem = product.query_selector("img.s-image")
                    image_url = img_elem.get_attribute("src") if img_elem else ""

                    # Construct product URL
                    product_url = f"https://www.amazon.de/dp/{asin}" if asin else ""

                    # Get description
                    description = name
                    try:
                        if product_url:
                            # Open product page in new tab
                            product_page = context.new_page()
                            product_page.goto(product_url, wait_until="domcontentloaded", timeout=10000)
                            time.sleep(2)

                            # Try to find product description
                            desc_elem = product_page.query_selector("#productDescription p")
                            if desc_elem:
                                additional_desc = desc_elem.inner_text().strip()
                                if additional_desc and len(additional_desc) > len(name):
                                    description = additional_desc

                            # If no description, try feature bullets
                            if description == name:
                                feature_bullets = product_page.query_selector_all("#feature-bullets li span.a-list-item")
                                if feature_bullets:
                                    bullet_points = []
                                    for bullet in feature_bullets[:5]:  # Limit to first 5 bullets
                                        bullet_text = bullet.inner_text().strip()
                                        if bullet_text and len(bullet_text) > 10:  # Filter out short/empty bullets
                                            bullet_points.append(bullet_text)
                                    if bullet_points:
                                        description = "• " + "\n• ".join(bullet_points)

                            product_page.close()
                    except Exception as e:
                        print(f"Error getting description for {name}: {e}")

                    results.append({
                        "name": name,
                        "price": price,
                        "image": image_url,
                        "url": product_url,
                        "description": description,
                        "relevance_score": relevance_score,
                        "score_details": score_details
                    })
                    found_count += 1

            browser.close()

    except Exception as e:
        print(f"Exception during Amazon search: {e}")

    # Sort results by relevance score (most relevant first)
    results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    return results

def search_amazon_advanced(query, limit=3, exact_match_only=False):
    """
    Advanced search with better filtering options
    """
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            # Try different search strategies
            search_variations = [
                query,
                f'"{query}"',  # Exact phrase search
                query.replace(' ', '+')
            ]

            for search_term in search_variations:
                if len(results) >= limit:
                    break

                url = f"https://www.amazon.de/s?k={search_term}"
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(3)

                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(2)

                products = page.query_selector_all("div[data-asin][data-component-type='s-search-result']")
                valid_products = [p for p in products if p.get_attribute("data-asin") and p.get_attribute("data-asin") != ""]

                for product in valid_products:
                    if len(results) >= limit:
                        break

                    asin = product.get_attribute("data-asin")

                    title_elem = product.query_selector("h2 a span") or product.query_selector("h2 span")
                    if not title_elem:
                        continue

                    name = title_elem.inner_text().strip()

                    # Apply stricter matching if exact_match_only is True
                    min_score = 50 if exact_match_only else 25
                    if not matches_query(name, query, min_score):
                        continue

                    # Check if we already have this product (by ASIN)
                    if any(r.get('asin') == asin for r in results):
                        continue

                    price_elem = product.query_selector("span.a-price span.a-offscreen")
                    price = price_elem.inner_text().strip() if price_elem else "Price not available"

                    img_elem = product.query_selector("img.s-image")
                    image_url = img_elem.get_attribute("src") if img_elem else ""

                    product_url = f"https://www.amazon.de/dp/{asin}" if asin else ""

                    relevance_score, _ = calculate_relevance_score(name, query)
                    results.append({
                        "name": name,
                        "price": price,
                        "image": image_url,
                        "url": product_url,
                        "asin": asin,
                        "relevance_score": relevance_score
                    })

            browser.close()

    except Exception as e:
        print(f"Exception during Amazon search: {e}")

    # Sort by relevance and return
    results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    return results[:limit]

if __name__ == "__main__":
    # Test with MacBook M4 Pro
    test_query = "macbook m4 pro"
    print(f"Searching for: '{test_query}'")
    print("=" * 50)

    # Use the improved search
    results = search_amazon(test_query, limit=3, max_pages=2)

    print(f"\nFound {len(results)} relevant results:")
    print("=" * 50)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Price: {result['price']}")
        print(f"   Relevance Score: {result.get('relevance_score', 0):.1f}")
        print(f"   URL: {result['url']}")
        print(f"   Description: {result['description'][:100]}...")

    # Test advanced search for exact matches
    print(f"\n\nAdvanced search (exact matches only):")
    print("=" * 50)

    advanced_results = search_amazon_advanced(test_query, limit=3, exact_match_only=True)

    for i, result in enumerate(advanced_results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Price: {result['price']}")
        print(f"   Relevance Score: {result.get('relevance_score', 0):.1f}")

    # Test with Apple Mouse query
    print(f"\n\nTesting with 'apple mouse' query:")
    print("=" * 50)

    mouse_results = search_amazon("apple mouse", limit=3, max_pages=2)

    for i, result in enumerate(mouse_results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Price: {result['price']}")
        print(f"   Relevance Score: {result.get('relevance_score', 0):.1f}")
        if 'score_details' in result:
            details = result['score_details']
            print(f"   Score breakdown: Exact:{details['exact_match']:.0f}, Order:{details['word_order']:.0f}, Coverage:{details['word_coverage']:.0f}, Brand:{details['brand_match']:.0f}")
