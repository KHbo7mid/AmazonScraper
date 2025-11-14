import time
import random
from playwright.sync_api import sync_playwright

class BaseScraper:
    def __init__(self,db_manager,headless: bool = True, base_url="https://www.amazon.com"):
        self.headless = headless
        self.db_manager = db_manager
        self.base_url = base_url
        
    def _random_delay(self, min_seconds: float=1.0, max_seconds: float=3.0):
        """Add random delay between operations"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def setup_browser(self):
        """Setup Playwright browser with anti-detection measures"""
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
            )

            # Add stealth scripts
            context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                """
            )

            return playwright, browser, context

        except Exception as e:
            self.logger.error(f"Browser setup failed: {e}")
            raise 