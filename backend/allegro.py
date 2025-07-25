from playwright.sync_api import sync_playwright
import time
import os
import random
import json
import sys
from urllib.parse import quote_plus

class AllegroScraper:
    def __init__(self, debug=False):
        self.debug = debug
        self.session_cookies = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def log(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    def wait_human_like(self, min_seconds=1.0, max_seconds=3.0):
        delay = random.uniform(min_seconds, max_seconds)
        self.log(f"Human-like delay: {delay:.2f}s")
        time.sleep(delay)

    def setup_stealth_context(self, playwright, attempt=0):
        """Setup browser context with stealth features"""
        user_agent = self.user_agents[attempt % len(self.user_agents)]

        # Randomize viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]
        viewport = viewports[attempt % len(viewports)]

        context_options = {
            "user_agent": user_agent,
            "viewport": viewport,
            "locale": "pl-PL",
            "timezone_id": "Europe/Warsaw",
            "color_scheme": "light",
            "device_scale_factor": 1.0,
            "is_mobile": False,
            "has_touch": False,
            "java_script_enabled": True,
            "accept_downloads": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
            "extra_http_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        }

        # Add saved cookies if available
        if self.session_cookies:
            context_options["storage_state"] = self.session_cookies

        return context_options

    def add_stealth_scripts(self, page):
        """Add stealth JavaScript to avoid detection"""
        stealth_js = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock languages and plugins
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pl-PL', 'pl', 'en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome runtime
        window.chrome = {
            runtime: {},
        };
        
        // Hide automation indicators
        Object.defineProperty(window, 'outerHeight', {
            get: () => window.innerHeight,
        });
        
        Object.defineProperty(window, 'outerWidth', {
            get: () => window.innerWidth,
        });
        """

        page.add_init_script(stealth_js)

    def simulate_human_mouse_movement(self, page):
        """Simulate realistic mouse movements"""
        viewport = page.viewport_size
        movements = random.randint(3, 7)

        for _ in range(movements):
            x = random.randint(50, viewport["width"] - 50)
            y = random.randint(50, viewport["height"] - 50)

            # Move with some randomness
            steps = random.randint(10, 30)
            page.mouse.move(x, y, steps=steps)
            self.wait_human_like(0.1, 0.5)

    def solve_captcha_if_present(self, page):
        """Handle CAPTCHA detection and solving"""
        captcha_indicators = [
            'div[class*="captcha"]',
            'iframe[src*="captcha"]',
            'div[class*="recaptcha"]',
            '.g-recaptcha',
            'text="captcha"',
            'text="robot"',
            'text="verification"'
        ]

        for indicator in captcha_indicators:
            try:
                element = page.wait_for_selector(indicator, timeout=2000)
                if element:
                    print("⚠️ CAPTCHA detected")
                    print("Please solve the CAPTCHA manually in the browser window.")
                    print("The script will wait for 2 minutes...")

                    # Take screenshot
                    os.makedirs("screenshots", exist_ok=True)
                    page.screenshot(path="screenshots/captcha_detected.png")

                    # Wait for CAPTCHA to be solved (check for products loading)
                    try:
                        page.wait_for_selector('article[data-role="offer"]', timeout=120000)
                        print("✅ CAPTCHA solved successfully!")
                        return True
                    except:
                        print("❌ CAPTCHA solving timeout")
                        return False
            except:
                continue

        return True  # No CAPTCHA found

    def get_product_data_from_json(self, page):
        """Try to extract product data from JSON-LD or window objects"""
        try:
            # Look for JSON-LD structured data
            json_scripts = page.query_selector_all('script[type="application/ld+json"]')
            for script in json_scripts:
                content = script.inner_text()
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        data = data[0]
                    if data.get('@type') == 'Product' or 'offers' in data:
                        self.log("Found JSON-LD product data")
                        return data
                except:
                    continue

            # Look for window.__NEXT_DATA__ or similar
            next_data = page.evaluate("""
                () => {
                    if (window.__NEXT_DATA__) return window.__NEXT_DATA__;
                    if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
                    if (window.App && window.App.initialState) return window.App.initialState;
                    return null;
                }
            """)

            if next_data:
                self.log("Found Next.js data")
                return next_data

        except Exception as e:
            self.log(f"Error extracting JSON data: {e}")

        return None

    def extract_products_advanced(self, page, limit=5):
        """Advanced product extraction with multiple strategies"""
        results = []

        # Strategy 1: Try to get data from JSON
        json_data = self.get_product_data_from_json(page)
        if json_data:
            # Parse JSON data for products (implementation depends on structure)
            pass

        # Strategy 2: Multiple selectors approach
        selector_combinations = [
            {
                'container': 'article[data-role="offer"]',
                'title': 'h2 a, h2 span, .offer-title',
                'price': '.price, [data-price], .offer-price',
                'link': 'a[href*="/oferta/"]',
                'image': 'img'
            },
            {
                'container': 'div[data-box-name*="listing"]',
                'title': 'h3, h2, .title',
                'price': '.price, .cost',
                'link': 'a',
                'image': 'img'
            },
            {
                'container': 'div.offer',
                'title': '.offer-title, h2, h3',
                'price': '.price, .amount',
                'link': 'a',
                'image': 'img'
            }
        ]

        for selectors in selector_combinations:
            try:
                containers = page.query_selector_all(selectors['container'])
                self.log(f"Found {len(containers)} containers with selector: {selectors['container']}")

                if not containers:
                    continue

                for container in containers[:limit * 2]:  # Get more than needed
                    try:
                        product = self.extract_single_product(container, selectors)
                        if product and len(results) < limit:
                            results.append(product)
                    except Exception as e:
                        self.log(f"Error extracting product: {e}")
                        continue

                if results:
                    break

            except Exception as e:
                self.log(f"Error with selector combination: {e}")
                continue

        return results[:limit]

    def extract_single_product(self, container, selectors):
        """Extract a single product from container"""
        try:
            # Title
            title_elem = container.query_selector(selectors['title'])
            if not title_elem:
                return None
            title = title_elem.inner_text().strip()

            # Price
            price_elem = container.query_selector(selectors['price'])
            price = price_elem.inner_text().strip() if price_elem else "Cena niedostępna"

            # Link
            link_elem = container.query_selector(selectors['link'])
            url = ""
            if link_elem:
                href = link_elem.get_attribute('href')
                if href:
                    url = href if href.startswith('http') else f"https://allegro.pl{href}"

            # Image
            img_elem = container.query_selector(selectors['image'])
            image = ""
            if img_elem:
                image = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ""

            # Generate description
            description = f"Produkt {title} dostępny na Allegro.pl w atrakcyjnej cenie."

            if title and url:
                return {
                    "name": title,
                    "price": price,
                    "url": url,
                    "image": image,
                    "description": description
                }

        except Exception as e:
            self.log(f"Error extracting single product: {e}")

        return None

    def search_with_api_fallback(self, query, limit=5):
        """Try to use unofficial API endpoints as fallback"""
        try:
            # Some sites expose search APIs - this is hypothetical for Allegro
            # You would need to reverse engineer their actual API endpoints
            self.log("Attempting API fallback (not implemented)")
            return []
        except:
            return []

    def search_allegro(self, query, limit=5, max_retries=2):
        """Main search function with improved anti-detection"""

        for attempt in range(max_retries + 1):
            try:
                self.log(f"Attempt {attempt + 1}/{max_retries + 1} for query: {query}")

                with sync_playwright() as p:
                    # Use different browser types on different attempts
                    browser_types = [p.chromium, p.firefox, p.webkit]
                    browser_type = browser_types[attempt % len(browser_types)]

                    # Launch browser with different settings
                    launch_options = {
                        "headless": False,  # Keep visible for CAPTCHA solving
                        "args": [
                            "--no-first-run",
                            "--disable-blink-features=AutomationControlled",
                            "--disable-features=VizDisplayCompositor",
                            "--disable-background-networking",
                            "--disable-background-timer-throttling",
                            "--disable-renderer-backgrounding",
                            "--disable-backgrounding-occluded-windows",
                            "--disable-component-extensions-with-background-pages",
                            "--no-default-browser-check",
                            "--no-first-run",
                            "--disable-default-apps",
                            "--disable-popup-blocking",
                            "--disable-translate",
                            "--disable-extensions",
                            "--allow-running-insecure-content",
                            "--disable-web-security",
                        ]
                    }

                    browser = browser_type.launch(**launch_options)

                    # Setup context with stealth features
                    context_options = self.setup_stealth_context(p, attempt)
                    context = browser.new_context(**context_options)

                    page = context.new_page()

                    # Add stealth scripts
                    self.add_stealth_scripts(page)

                    # Step 1: Visit homepage first (more natural)
                    self.log("Visiting Allegro homepage...")
                    page.goto("https://allegro.pl/", wait_until="domcontentloaded", timeout=60000)

                    # Simulate human behavior
                    self.wait_human_like(2, 4)
                    self.simulate_human_mouse_movement(page)

                    # Check if we're blocked immediately
                    if self.is_blocked(page):
                        self.log("Blocked on homepage, trying different approach")
                        browser.close()
                        continue

                    # Step 2: Perform search
                    search_success = self.perform_search(page, query)
                    if not search_success:
                        self.log("Search failed, trying next attempt")
                        browser.close()
                        continue

                    # Step 3: Handle CAPTCHA if present
                    if not self.solve_captcha_if_present(page):
                        self.log("CAPTCHA solving failed")
                        browser.close()
                        continue

                    # Step 4: Wait for results and extract
                    self.wait_human_like(3, 5)

                    # Scroll to load more content
                    self.scroll_page_naturally(page)

                    # Extract products
                    results = self.extract_products_advanced(page, limit)

                    # Save session for future use
                    try:
                        self.session_cookies = context.storage_state()
                    except:
                        pass

                    browser.close()

                    if results:
                        self.log(f"Successfully extracted {len(results)} products")
                        return results
                    else:
                        self.log("No products found, trying next attempt")

            except Exception as e:
                self.log(f"Attempt {attempt + 1} failed: {e}")
                try:
                    browser.close()
                except:
                    pass

                if attempt < max_retries:
                    wait_time = random.uniform(5, 15) * (attempt + 1)
                    self.log(f"Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)

        # If all attempts failed, try API fallback
        self.log("All attempts failed, trying API fallback")
        return self.search_with_api_fallback(query, limit)

    def is_blocked(self, page):
        """Check if we're blocked or facing anti-bot measures"""
        blocking_indicators = [
            'text="blocked"',
            'text="robot"',
            'text="captcha"',
            'text="verification"',
            'text="unusual traffic"',
            '.captcha',
            '#captcha'
        ]

        for indicator in blocking_indicators:
            try:
                if page.query_selector(indicator):
                    return True
            except:
                continue

        # Check for redirect to blocked page
        if "blocked" in page.url.lower() or "captcha" in page.url.lower():
            return True

        return False

    def perform_search(self, page, query):
        """Perform search with human-like behavior"""
        try:
            # Method 1: Use search box
            search_selectors = [
                'input[data-role="search-input"]',
                'input[name="string"]',
                'input[placeholder*="szukaj"]',
                '#search-input',
                '.search-input'
            ]

            search_box = None
            for selector in search_selectors:
                search_box = page.query_selector(selector)
                if search_box:
                    break

            if search_box:
                self.log("Found search box, typing query...")

                # Click and focus
                search_box.click()
                self.wait_human_like(0.5, 1.0)

                # Clear existing text
                search_box.fill("")
                self.wait_human_like(0.2, 0.5)

                # Type with human-like delays
                for char in query:
                    search_box.type(char)
                    time.sleep(random.uniform(0.05, 0.15))

                self.wait_human_like(0.5, 1.5)

                # Submit search
                search_box.press("Enter")
                page.wait_for_load_state("domcontentloaded")

                return True
            else:
                # Method 2: Direct URL navigation
                self.log("No search box found, using direct URL")
                search_url = f"https://allegro.pl/listing?string={quote_plus(query)}"
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                return True

        except Exception as e:
            self.log(f"Search failed: {e}")
            return False

    def scroll_page_naturally(self, page):
        """Scroll page like a human would"""
        viewport_height = page.viewport_size["height"]

        # Multiple small scrolls
        scroll_attempts = random.randint(3, 6)
        for i in range(scroll_attempts):
            scroll_distance = random.randint(200, 600)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")

            # Wait and sometimes scroll back up a bit
            self.wait_human_like(1, 3)
            if random.random() > 0.7:  # 30% chance to scroll back
                back_scroll = random.randint(50, 200)
                page.evaluate(f"window.scrollBy(0, -{back_scroll})")
                self.wait_human_like(0.5, 1.5)

def search_allegro_improved(query, limit=5, max_retries=2, debug=False):
    """
    Improved Allegro search function

    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        max_retries (int): Maximum retry attempts
        debug (bool): Enable debug logging

    Returns:
        list: List of product dictionaries
    """
    scraper = AllegroScraper(debug=debug)
    return scraper.search_allegro(query, limit, max_retries)

# Mock data function for testing/fallback
def get_mock_allegro_data(query, limit=5):
    """Generate mock data for testing"""
    products = []

    base_prices = [1299, 1899, 2499, 3199, 4299]
    colors = ["Czarny", "Biały", "Niebieski", "Czerwony", "Zielony"]

    for i in range(min(limit, 5)):
        price = base_prices[i % len(base_prices)] + random.randint(-200, 200)
        color = colors[i % len(colors)]

        products.append({
            "name": f"{query.title()} {color} - Model {i+1}",
            "price": f"{price},00 zł",
            "url": f"https://allegro.pl/oferta/mock-product-{i+1}-{random.randint(10000, 99999)}",
            "image": f"https://example.com/image{i+1}.jpg",
            "description": f"Wysokiej jakości {query} w kolorze {color.lower()}. Dostępny na Allegro.pl."
        })

    return products

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Improved Allegro.pl scraper')
    parser.add_argument('query', nargs='?', default="iphone 13", help='Search query')
    parser.add_argument('--limit', type=int, default=5, help='Number of products to return')
    parser.add_argument('--retries', type=int, default=2, help='Max retry attempts')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--mock', action='store_true', help='Use mock data only')

    args = parser.parse_args()

    print(f"Searching for: '{args.query}'")
    print("=" * 50)

    if args.mock:
        print("Using mock data...")
        results = get_mock_allegro_data(args.query, args.limit)
    else:
        print("Using improved scraper...")
        results = search_allegro_improved(
            query=args.query,
            limit=args.limit,
            max_retries=args.retries,
            debug=args.debug
        )

    if results:
        print(f"\nFound {len(results)} products:")
        for i, product in enumerate(results, 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: {product['price']}")
            print(f"   URL: {product['url']}")
            print()
    else:
        print("No products found.")

    print("\nTips for better results:")
    print("- Use Polish search terms when possible")
    print("- Try different retry counts with --retries")
    print("- Enable debug mode with --debug for more info")
    print("- Use --mock for testing without scraping")