from fastapi import APIRouter, HTTPException

from app.scraper.amazon_scraper import AmazonScraper  # Make sure this import matches your scraper

router = APIRouter()

@router.post("/scrape")
def scrape_products():  
    """Synchronous endpoint for synchronous scraping"""
    try:
        scraper = AmazonScraper()
        result = scraper.run_full_scraping(max_categories=3, max_subcategories=5, max_products=10)  
        
        return {
            "message": f"Scraping completed! Added {result} products",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during scraping: {str(e)}")