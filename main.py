from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import products, categories, deals , scrape
import uvicorn


app = FastAPI(
    title="Amazon Best Deals API",
    description="API for querying and filtering Amazon product deals",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(categories.router, prefix="/api", tags=["categories"])
app.include_router(deals.router, prefix="/api", tags=["deals"])
app.include_router(scrape.router, prefix="/api", tags=["scraping"])  





if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
