# Amazon Product Scraper & Deals Finder

This project scrapes product data from Amazon, stores it in a database, and provides an API + simple UI to search and filter the best deals.

# 🚀 What it does

Scrapes Amazon categories and product details (title, brand, prices, discount, rating, reviews, image, availability).

Saves all data into a structured database (PostgreSQL).

Exposes a FastAPI backend with filtering, sorting, and pagination.

Provides a /best-deals endpoint to get products with the highest discount + best rating.

Includes a small Streamlit frontend to search and visualize deals.

# 🔧 How it works

* Scraper (Playwright)
Collects product data from Amazon pages and returns clean structured information.

* Database Layer
Stores categories and products for fast queries.

* FastAPI Backend
Provides endpoints:

/products → Get all products with filters

/scrape -> run scraping process

/products/{product_id} → get product by ID 

/best-deals → Highest discounts

/categories → List categories

* Frontend (Streamlit)
Simple interface where users can search, filter, and view deals.

# ▶️ Run the project
`pip install -r requirements.txt`
`playwright install`
`uvicorn api.main:app --reload`
`streamlit run frontend/app.py`