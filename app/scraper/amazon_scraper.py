from playwright.sync_api import sync_playwright
import time, random, logging
from typing import List, Dict
from urllib.parse import urljoin
from app.database.database_manager import DBManager
from app.utils.logger import setup_logger
from .CategoryScraper import CategoryScraper
from .ProductScraper import ProductScraper

class AmazonScraper:
    def __init__(self, headless: bool = True):
        self.db_manager = DBManager()
        self.category_scraper = CategoryScraper(self.db_manager, headless)
        self.product_scraper = ProductScraper(self.db_manager, headless)
        self.logger = setup_logger(__name__)
    
    def run_full_scraping(self, max_categories: int = 5, max_subcategories: int = 10, max_products: int = 10):
        """Complete workflow: scrape categories -> scrape products -> save to DB"""
        print("Starting full workflow: categories -> products")
        
        
        categories = self.category_scraper.scrape_and_save_categories(
            max_categories=max_categories, 
            max_subcategories=max_subcategories
        )
        print(f"Scraped {len(categories)} categories")
        
        # 2. Scrape products for each category
        for category in categories:
            print(f"Scraping products for category: {category['name']}") 
            self.product_scraper.scrape_products_and_save_to_database(
               category_id=category['id'],
                category_name=category['name'],
                category_url=category['url'],
                max_products=max_products
            )
            self.logger.info(f"Completed scraping for category: {category['name']}")
    
    def scrape_products_for_existing_categories(self, max_products: int = 10):
        """Workflow 2: Get categories from DB -> scrape products"""
        
        
        
        categories = self.db_manager.get_all_categories()
        print(f"Found {len(categories)} categories in database")
        
        if not categories:
            print("No categories found in database. Run full workflow first.")
            return
        
        
        for category in categories:
            print(f"Scraping products for category: {category['name']}") 
            self.product_scraper.scrape_products_and_save_to_database(
                category_url=category['url'],   
                category_name=category['name'],
                category_id=category['id'],
                max_products=max_products
            )
            self.logger.info(f"Completed scraping for category: {category['name']}")