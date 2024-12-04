from fastapi import FastAPI
from . endpoints import products

app = FastAPI()
app.include_router(products.router, prefix="/productsapi", tags=["products"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Products API. Your favourite Products API for your store!"}