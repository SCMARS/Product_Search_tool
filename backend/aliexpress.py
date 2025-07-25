from playwright.sync_api import sync_playwright, TimeoutError
import time
import json

def search_aliexpress_playwright(query: str, limit: int = 3) -> list[dict]:
    """
    Fast AliExpress product search using Playwright:
    - headless mode
    - blocks unnecessary resources
    - auto-detects product containers
    - takes a debug screenshot on failure
    """
    results = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # headful to capture debug screenshot
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                "Gecko/20100101 Firefox/121.0"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US"
        )

        # Block styles/fonts/media to speed up
        def block_route(route, request):
            if request.resource_type in ("stylesheet", "font", "media"):
                return route.abort()
            route.continue_()
        context.route("**/*", block_route)

        page = context.new_page()
        search_url = f"https://www.aliexpress.com/wholesale?SearchText={query.replace(' ', '+')}"
        page.goto(search_url, wait_until="domcontentloaded", timeout=20000)

        # Scroll a bit to trigger lazy load
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(2)

        # Take debug screenshot
        page.screenshot(path="aliexpress_debug.png", full_page=True)

        # Try updated selectors for product containers
        container_selectors = [
            'div._1NoI8',  # common item wrapper
            'div._3t7zg',  # newer card wrapper
            'div._2JxJG'   # grid cell
        ]
        product_containers = []
        for sel in container_selectors:
            nodes = page.query_selector_all(sel)
            if nodes:
                print(f"✅ Found {len(nodes)} containers with selector: {sel}")
                product_containers = nodes
                break

        if not product_containers:
            print("❌ No product containers found, see aliexpress_debug.png for DOM")
            browser.close()
            return results

        # Process up to `limit` products
        for idx, container in enumerate(product_containers[:limit], start=1):
            try:
                name_el = container.query_selector("a._3t7zg ._18_85") or container.query_selector("h1, h2, h3")
                price_el = container.query_selector("span._12A8D")
                link_el = container.query_selector("a._3t7zg, a.JIIxO") or container.query_selector("a[href*='/item/']")
                img_el  = container.query_selector("img")

                name = name_el.inner_text().strip() if name_el else "No name"
                price = price_el.inner_text().strip() if price_el else "No price"
                href = link_el.get_attribute("href") if link_el else ""
                image_url = img_el.get_attribute("src") or img_el.get_attribute("data-src") or "" if img_el else ""

                # Normalize URL
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.aliexpress.com" + href

                results.append({
                    "name": name,
                    "price": price,
                    "url": href,
                    "image": image_url,
                    "description": name
                })
                print(f"✅ [{idx}] {name} | {price}")
            except Exception as e:
                print(f"⚠️ Error parsing product #{idx}: {e}")

        browser.close()

    return results

if __name__ == "__main__":
    test_query = "iphone 16 pro max"
    print(f"🧪 Testing search for '{test_query}'…")
    products = search_aliexpress_playwright(test_query, limit=5)
    print(f"\n📊 Found {len(products)} products:\n")
    for i, prod in enumerate(products, 1):
        print(f"{i}. {prod['name']}")
        print(f"   Price: {prod['price']}")
        print(f"   URL:   {prod['url']}")
        print(f"   Image: {prod['image']}\n")

    with open(f"aliexpress_results_{test_query.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print("💾 Results saved to JSON.")
