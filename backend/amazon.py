from playwright.sync_api import sync_playwright
import time

def search_amazon(query, limit=3):
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Headless mode for production
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = context.new_page()

            url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded")

            time.sleep(3)  # Wait for content to load

            # Scroll down to load all blocks
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(3)

            # Product selector
            products = page.query_selector_all("div[data-asin][data-component-type='s-search-result']")


            valid_products = [p for p in products if p.get_attribute("data-asin") and p.get_attribute("data-asin") != ""]

            count = 0
            for product in valid_products:
                if count >= limit:
                    break


                asin = product.get_attribute("data-asin")

                # Check if title exists - try multiple selectors
                title_elem = product.query_selector("h2 a span")
                if not title_elem:
                    title_elem = product.query_selector("h2 span")
                if not title_elem:
                    continue

                name = title_elem.inner_text().strip()

                price_elem = product.query_selector("span.a-price span.a-offscreen")
                price = price_elem.inner_text().strip() if price_elem else "Price not available"

                img_elem = product.query_selector("img.s-image")
                image_url = img_elem.get_attribute("src") if img_elem else ""


                if asin:
                    product_url = f"https://www.amazon.de/dp/{asin}"
                else:
                    product_url = ""

                description = name


                try:
                    # Open product page in a new tab
                    product_page = context.new_page()
                    product_page.goto(product_url, wait_until="domcontentloaded")
                    time.sleep(2)

                    # Try to find product description
                    desc_elem = product_page.query_selector("#productDescription p")
                    if desc_elem:
                        additional_desc = desc_elem.inner_text().strip()
                        if additional_desc:
                            description = additional_desc

                    # If no description found, try feature bullets
                    if description == name:
                        feature_bullets = product_page.query_selector_all("#feature-bullets li span")
                        if feature_bullets:
                            bullet_points = [bullet.inner_text().strip() for bullet in feature_bullets]
                            if bullet_points:
                                description = "\n• " + "\n• ".join(bullet_points)

                    # Close the product page tab
                    product_page.close()
                except Exception as e:
                    print(f"Error getting description for {name}: {e}")
                    # If there's an error, just use the name as description
                    description = name

                results.append({
                    "name": name,
                    "price": price,
                    "image": image_url,
                    "url": product_url,
                    "description": description
                })
                count += 1

            browser.close()
    except Exception as e:
        print(f"Exception during Amazon search: {e}")

    return results

if __name__ == "__main__":
    test_query = "iphone 16 pro "
    res = search_amazon(test_query)
    print(f"Found {len(res)} results for '{test_query}':")
    for i, r in enumerate(res, 1):
        print(f"{i}. {r['name']} - {r['price']}")
        print(f"   {r['url']}")
