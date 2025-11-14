from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.database.database_manager import DBManager
from app.model.schemas import Product

router = APIRouter()
db = DBManager()

@router.get("/best-deals", response_model=List[Product])
async def get_best_deals(limit: int = Query(10, ge=1, le=50)):
    
    deals = db.get_best_deals(limit=limit)
    return deals