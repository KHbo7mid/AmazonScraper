from fastapi import FastAPI,HTTPException
from typing import List, Optional
from app.database.database_manager import DBManager
from app.model.schemas import Category, Product


app = FastAPI(title="Amazon Best Deals API")
db = DBManager()

@app.get("/")
async def root():
    return {"message": "Welcome to the Amazon Best Deals API"}

@app.get("/categories", response_model=List[Category])
async def get_categories():
    categories = db.get_all_categories()
    return categories

@app.get("/products", response_model=List[Product])
async def get_products( limit: Optional[int] = 10,offset: Optional[int] = 0):
    products = db.get_products()
    return products

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    product = db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product[0]
