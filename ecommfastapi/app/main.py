from fastapi import FastAPI
from app.account.routers import router as account_router
from app.product.routers.category import router as category_router

app = FastAPI(title="FastAPI E-commerce Backend")

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI E-commerce Backend!"}

app.include_router(account_router, prefix="/app/account", tags=["Account"])
app.include_router(category_router, prefix="/app/product", tags=["Categories"])