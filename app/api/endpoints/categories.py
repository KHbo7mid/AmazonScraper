from fastapi import APIRouter, HTTPException
from typing import List
from app.database.database_manager import DBManager
from app.model.schemas import Category

router = APIRouter()
db = DBManager()

@router.get("/categories", response_model=List[Category])
async def get_categories():
    try:
        categories = db.get_all_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")