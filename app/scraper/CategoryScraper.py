from typing import List, Dict
from urllib.parse import urljoin
import time
from app.utils.logger import setup_logger
from .BaseScraper import BaseScraper
class CategoryScraper(BaseScraper):
    def __init__(self, db_manager,headless: bool = True, base_url="https://www.amazon.com"):
        super().__init__(db_manager,headless,base_url)
        self.logger = setup_logger(__name__)  
        
    
    
    def open_hamburger_menu(self, page):
        """Open the hamburger menu with fallback strategies"""
        try:
            menu = page.wait_for_selector("#nav-hamburger-menu", timeout=10000)
            menu.scroll_into_view_if_needed()
            menu.click(force=True)
            return True
        except Exception as e:
            self.logger.warning(f"Hamburger menu not loaded: {e}, trying Amazon logo...")
            try:
                logo = page.wait_for_selector("#nav-bb-logo", timeout=5000)
                logo.click(force=True)
                self._random_delay(2, 4)
                menu = page.wait_for_selector("#nav-hamburger-menu", timeout=10000)
                menu.scroll_into_view_if_needed()
                menu.click(force=True)
                return True
            except Exception as e2:
                self.logger.error(f"Failed to open hamburger menu after clicking logo: {e2}")
                return False
    
    def get_main_categories(self, page,max_categories: int = 5) -> List:
        """Extract main categories from the menu"""
        section = page.query_selector('section[aria-labelledby="Shop by Department"]') \
                  or page.query_selector('#hmenu-content')
        if not section:
            self.logger.warning("Could not find main department section.")
            return []
        
        main_categories = section.query_selector_all("a.hmenu-item")[:max_categories]
        self.logger.info(f"Found {len(main_categories)} main categories")
        return main_categories
    
    def handle_see_all_category(self, page, cat, name):
        """Handle 'See All' category click"""
        try:
            page.evaluate("(element) => element.click()", cat)
            self._random_delay(1, 2)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to click 'See All' for {name}: {e}")
            return False
    
    def scroll_and_click_category(self, page, cat, name):
        """Scroll to and click on a category"""
        try:
            # Scroll inside menu container
            page.evaluate("""
                (el) => {
                    const container = document.querySelector('#hmenu-content');
                    container.scrollTop = el.offsetTop - container.offsetTop;
                }
            """, cat)
            self._random_delay(0.5, 1.5)
            page.evaluate("(element) => element.click()", cat)
            return True
        except Exception as e:
            self.logger.warning(f"Click failed for {name}: {e}")
            return False
    
    def extract_subcategories(self, page, main_category_name):
        """Extract subcategories for a given main category"""
        try:
            # Wait for the SPECIFIC category section to load
            page.wait_for_selector(f'section[aria-labelledby="{main_category_name}"]', timeout=10000)
            self._random_delay(1, 2)
            
            # Get subcategories from the specific category section
            category_section = page.query_selector(f'section[aria-labelledby="{main_category_name}"]')
            if not category_section:
                self.logger.warning(f"Could not find section for category: {main_category_name}")
                return []
            
            subcats = category_section.query_selector_all("a.hmenu-item")
            
            # Filter subcategories
            filtered_subcats = []
            for subcat in subcats:
                sub_name = subcat.text_content().strip()
                sub_url = subcat.get_attribute("href")
                
                if sub_name and sub_url and len(sub_name) > 2:
                    filtered_subcats.append(subcat)
            
            self.logger.info(f"Found {len(filtered_subcats)} actual subcategories under {main_category_name}")
            return filtered_subcats
            
        except Exception as e:
            self.logger.warning(f"Failed to extract subcategories for {main_category_name}: {e}")
            return []
    
    def navigate_back_to_main_menu(self, page):
        """Navigate back to the main menu"""
        back_button = page.query_selector("a.hmenu-item.hmenu-back-button")
        if back_button:
            page.evaluate("(element) => element.click()", back_button)
            # Wait for main menu to actually reload
            page.wait_for_selector('section[aria-labelledby="Shop by Department"]', timeout=8000)
            time.sleep(2)
            return True
        else:
            # Fallback - refresh and re-open menu
            page.reload()
            self._random_delay(3, 5)
            menu = page.wait_for_selector("#nav-hamburger-menu", timeout=10000)
            menu.click(force=True)
            page.wait_for_selector("#hmenu-content", timeout=15000)
            return False

    def scrape_and_save_categories(self,max_categories:int =5,max_subcategories:int =10) -> List[Dict[str, str]]:
        """Main method to scrape categories and save them to database"""
        categories = []
        try:
            playwright, browser, context = self.setup_browser()
            page = context.new_page()
            page.goto(self.base_url, wait_until="load", timeout=60000)
            self._random_delay(3, 6)

            # Open hamburger menu
            if not self.open_hamburger_menu(page):
                return []

            self._random_delay(2, 4)
            page.wait_for_selector("#hmenu-content", timeout=15000)

            # Get main categories
            main_categories = self.get_main_categories(page,max_categories=max_categories)
            if not main_categories:
                return []

            for cat in main_categories:
                name = cat.text_content().strip()
                if not name:
                    continue

                self.logger.info(f"Opening main category: {name}")

                # Check for "See All"
                if name.lower() == "see all":
                    self.handle_see_all_category(page, cat, name)
                    continue

                # Scroll and click category
                if not self.scroll_and_click_category(page, cat, name):
                    continue

                # Extract subcategories
                subcats = self.extract_subcategories(page, name)
                
                for subcat in subcats[:max_subcategories]:
                    sub_name = subcat.text_content().strip()
                    sub_url = subcat.get_attribute("href")
                    if sub_name and sub_url:
                        full_name = f"{name} > {sub_name}"
                        full_url = urljoin(self.base_url, sub_url)
                        
                        
                        try:
                            category_id = self.db_manager.insert_category(full_name, full_url)
                            categories.append({
                                "id": category_id,
                                "name": full_name, 
                                "url": full_url
                            })
                            self.logger.info(f"ADDED to DB: {full_name} (ID: {category_id})")
                        except Exception as e:
                            self.logger.error(f"Failed to insert category '{full_name}': {e}")

                # Navigate back to main menu
                self.navigate_back_to_main_menu(page)

            self.logger.info(f"Total categories scraped and saved: {len(categories)}")
            return categories

        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return []

        finally:
            try:
                context.close()
                browser.close()
                playwright.stop()
            except Exception as e:
                self.logger.debug(f"Cleanup error: {e}")