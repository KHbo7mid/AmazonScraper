from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: float = 0.0
    rating: Optional[float] = None
    reviews_count: int = 0
    product_link: str
    image_url: Optional[str] = None
    availability: Optional[str] = None

class ProductCreate(ProductBase):
    category_id: int

class Product(ProductBase):
    id: int
    category_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    url: str



class Category(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    limit: int
    total_pages: int

class FilterParams(BaseModel):
    category_id: Optional[int] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_discount: Optional[float] = None
    min_rating: Optional[float] = None
    sort_by: str = "id"
    sort_order: str = "DESC"

class BestDealsParams(BaseModel):
    limit: int = 10
    min_discount: float = 20.0
    min_rating: float = 4.0