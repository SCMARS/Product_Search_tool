from playwright.sync_api import sync_playwright
import time

def search_amazon(query, limit=3):
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Чтобы видеть браузер
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = context.new_page()

            url = f"https://www.amazon.de/s?k={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded")

            time.sleep(3)  # Подождать подгрузку

            # Скроллим вниз, чтобы загрузить все блоки
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(3)

            # Новый селектор товаров
            products = page.query_selector_all("div[data-asin][data-component-type='s-search-result']")
            print(f"Found {len(products)} products")

            count = 0
            for product in products:
                if count >= limit:
                    break
                # Проверяем есть ли заголовок
                title_elem = product.query_selector("h2 a span")
                if not title_elem:
                    continue
                name = title_elem.inner_text().strip()

                price_elem = product.query_selector("span.a-price span.a-offscreen")
                price = price_elem.inner_text().strip() if price_elem else "Price not available"

                img_elem = product.query_selector("img.s-image")
                image_url = img_elem.get_attribute("src") if img_elem else ""

                link_elem = product.query_selector("h2 a.a-link-normal")
                relative_url = link_elem.get_attribute("href") if link_elem else ""
                product_url = f"https://www.amazon.de{relative_url}" if relative_url.startswith("/") else relative_url

                results.append({
                    "name": name,
                    "price": price,
                    "image": image_url,
                    "url": product_url
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
