from app.scraper.amazon_scraper import AmazonScraper
from app.database.database_manager import DBManager
if __name__ == "__main__":
    db_manager = DBManager()

    scraper = AmazonScraper(headless=True)
    scraper.scrape_products_for_existing_categories(max_products=10)
   