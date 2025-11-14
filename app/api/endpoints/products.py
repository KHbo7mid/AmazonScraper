from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.database.database_manager import DBManager
from app.model.schemas import Product, ProductResponse

router = APIRouter()
db = DBManager()

@router.get("/products", response_model=ProductResponse)
async def get_products(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_discount: Optional[float] = Query(None, ge=0, le=100, description="Minimum discount percentage"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    sort_by: str = Query("id", description="Sort by field (id, price, discount_percent, rating)"),
    sort_order: str = Query("DESC", description="Sort order (ASC, DESC)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    try:
        offset = (page - 1) * limit
        products, total_count = db.get_products(
            category_id=category_id,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            min_discount=min_discount,
            min_rating=min_rating,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        total_pages = (total_count + limit - 1) // limit
        
        return ProductResponse(
            products=products,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    product = db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


    
    
