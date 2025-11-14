from typing import List, Dict,Optional
from urllib.parse import urljoin
import time,random
import  re 
from app.utils.logger import setup_logger
from .BaseScraper import BaseScraper
class ProductScraper(BaseScraper):
    def __init__(self, db_manager, headless: bool = True, base_url="https://www.amazon.com"):
        super().__init__(db_manager, headless, base_url)
        self.logger = setup_logger(__name__)  
        
        
    def scrape_products_from_category(self,category,max_products:int=10)->List[Dict]:
        """Scrape products from a given category URL"""
        products = []
        try:
            playwright, browser, context = self.setup_browser()
            page = context.new_page()
            self.logger.info(f"Navigating to category: {category.name}")
            page.goto(category.url,wait_until='load', timeout=60000)
            self._random_delay(2, 5)
            
            
            page.wait_for_selector("[data-component-type='s-search-result']", timeout=15000)

            product_cards = page.query_selector_all("[data-component-type='s-search-result']")[:max_products]
            self.logger.info(f"Found {len(product_cards)} products in category {category.name}")
            for i,product in enumerate(product_cards):
                try:
                    product_data=self._extract_product_data(product,category.name,category.id)
                    if product_data:
                        products.append(product_data)
                        self.logger.info(f"Scraped product {i+1}: {product_data['title'][:50]}...")
                        
                except Exception as e:
                        self.logger.warning(f"Failed to extract product {i+1}: {e}")
                        continue
                    
            for product_data in products:
                if product_data["product_link"]:
                    product_data["brand"] = self._extract_brand(page, product_data["product_link"])
            
        
                    
            self.logger.info(f"Scraping completed for category {category.name}. Total products scraped: {len(products)}")
            return products
        except Exception as e:
            self.logger.error(f"Error scraping products from category {category.name}: {e}")
            return []
        finally:
            try:
                page.close()
                browser.close()
                playwright.stop()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
            

    def _extract_product_data(self, product_card, category_name:str,category_id:int)->Optional[Dict]:
        """Extract product data from a product card element"""
        try:
             # Extract title
            title_element = product_card.query_selector("a h2 span")
            title = title_element.text_content().strip() if title_element else None
            
            if not title:
                return None

            # Extract product URL
            link_element = product_card.query_selector("a.a-link-normal")
            product_link = link_element.get_attribute("href") if link_element else None
            if product_link:
                product_link = urljoin(self.base_url, product_link)
                
                
            

            # Extract price information
            price_data = self._extract_price_data(product_card)

            # Extract rating and reviews
            rating_data = self._extract_rating_data(product_card)
            
            # Extract image URL
            image_element = product_card.query_selector(".s-image")
            image_url = image_element.get_attribute("src") if image_element else None
            
            # Extract availability
            availability = self._extract_availability(product_card)

            product_data = {
                "category_id": category_id,
                "category_name": category_name,
                "title": title,
                "brand": "Unknown",
                "price": price_data["current_price"] if price_data else None,
                "original_price": price_data["original_price"] if price_data else None,
                "discount_percent": price_data["discount_percent"] if price_data else None,
                "rating": rating_data["rating"]if rating_data else None,
                "reviews_count": rating_data["reviews_count"] if rating_data else None,
                "product_link": product_link,
                "image_url": image_url,
                "availability": availability,
                
            }
            return product_data
        except Exception as e:
            self.logger.error(f"Error extracting product data: {e}")
            return {}
        
        
    def _extract_price_data(self, product_element) -> Dict:
        """Extract price, original price, and discount percentage"""
        try:
            # Current price
            price_element = product_element.query_selector(".a-price .a-offscreen")
            current_text = price_element.text_content().strip() if price_element else "0"
            current_price=self._clean_price(current_text)
            
            # Original price (for discounts)
            original_price_element = product_element.query_selector(".a-price.a-text-price .a-offscreen")
            original_price_text = original_price_element.text_content().strip() if original_price_element else current_price
            
            original_price=self._clean_price(original_price_text)
            
            # Calculate discount percentage
            discount_percent = 0
            if original_price != current_price:
                try:
                    # Extract numeric values from price strings
                    current_num = float(re.sub(r'[^\d.]', '', current_price))
                    original_num = float(re.sub(r'[^\d.]', '', original_price))
                    if original_num > 0:
                        discount_percent = int(((original_num - current_num) / original_num) * 100)
                except:
                    discount_percent = 0

            return {
                "current_price": current_price,
                "original_price": original_price,
                "discount_percent": discount_percent
            }
            
        except Exception as e:
            self.logger.debug(f"Could not extract price data: {e}")
            return {"current_price": "0", "original_price": "0", "discount_percent": 0}
        
        
    def _clean_price(self, price_text: str) -> float:
        """Convert price string to numeric value"""
        try:
            # Remove dollar sign, commas, and any non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', price_text)
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
        
    def _extract_rating_data(self, product_element) -> Dict:
        """Extract rating and review count"""
        try:
            # Rating
            rating_element = product_element.query_selector(".a-icon-alt")
            rating_text = rating_element.text_content().strip() if rating_element else ""
            
            # Extract numeric rating
            rating_match = re.search(r"(\d+\.\d+)", rating_text)
            rating = rating_match.group(1) if rating_match else "0"
            
            # Review count
            reviews_element = product_element.query_selector(".a-size-mini.puis-normal-weight-text.s-underline-text")
            reviews_text = reviews_element.text_content().strip() if reviews_element else "0"
            
            # Convert review text to number (e.g., "1,234" -> 1234)
            reviews_count = 0
            if reviews_text and reviews_text != "0":
                try:
                    reviews_count = int(re.sub(r'[^\d]', '', reviews_text))
                except:
                    reviews_count = 0

            return {
                "rating": rating,
                "reviews_count": reviews_count
            }
            
        except Exception as e:
            self.logger.debug(f"Could not extract rating data: {e}")
            return {"rating": "0", "reviews_count": 0}
        
    
        
    def _extract_availability(self, product_element) -> str:
        """Check product availability"""
        try:
            # Check for out of stock indicators
            availability_span = product_element.query_selector(
            ".a-size-base.a-color-price"
        )
            if availability_span:
                return availability_span.text_content().strip()
                
            
            return "In Stock"
            
        except Exception as e:
            self.logger.debug(f"Could not determine availability: {e}")
            return "In Stock"
    
    def _extract_brand(self,page, product_url: str) -> str:
        """Navigate to product page and extract brand information"""
        try:
            # Save current URL to navigate back later
            current_url = page.url
            
            # Navigate to product page
            page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            self._random_delay(2, 3)
            
            # Try the bylineInfo element
            brand_element = page.query_selector("#bylineInfo")
            if brand_element:
                brand = brand_element.text_content().strip()
                if brand and len(brand) > 1:
                    brand = brand.replace("Brand: ", "").replace("Visit the ", "").replace(" Store", "")
                    brand = brand.strip()
                    return brand
            
            return "Unknown"
            
        except Exception as e:
            self.logger.warning(f"Could not extract brand from product page {product_url}: {e}")
            return "Unknown"
        finally:
            # Always navigate back to search results
            try:
                page.goto(current_url, wait_until="domcontentloaded")
                self._random_delay(1, 2)
            except Exception as e:
                self.logger.debug(f"Could not navigate back to search results: {e}")
                
                
    def scrape_products_and_save_to_database(self,category_id:int,category_name:str,category_url:str, max_products: int = 20):
        """Save scraped products to the database"""
        products = self.scrape_products_from_category(
            category=type("Category", (object,), {"id": category_id, "name": category_name, "url": category_url})(),
            max_products=max_products
        )
        for product in products:
            self.db_manager.insert_product(product)
        self.logger.info(f"Saved {len(products)} products to the database for category {category_name}.")