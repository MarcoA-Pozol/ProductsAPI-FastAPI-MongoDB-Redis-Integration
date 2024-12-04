from fastapi import APIRouter, HTTPException, Depends
from app.schemas import Product
from app.database import get_database
from bson import ObjectId
from typing import List
# Cache 
from ..redis.utils import save_hash, get_hash, delete_hash

router = APIRouter()

# List Products
@router.get("/products/", response_model=List(Product))
async def list_products():
    """
        Lists all the products from MongoDB products collection and retrieve it.
    """
    db = await get_database()
    list_of_products = await db["products"].find().to_list(20)
    
    if list_of_products is None:
        raise HTTPException(status_code=404, detail="No any product was found.")
    
    # Convert MongoDB documents to Products objects
    return [
        Product(id=str(product["_id"]), **{key: product[key] for key in product if key != "_id"})
        for product in list_of_products
    ]
    
# Retrieve specific product
@router.get("/products/{product_id}", response_model=Product)
async def retrieve_product(product_id):
    """
        Retrieves a specific Product by their ObjectID.
    """
    try:
        # Check if requested object exists in cache and get it
        data = get_hash(key=product_id)
        print(f"Fetching data from Cache: {data}")
        # If not exists in cache, get from DB
        if not data:
            db = await get_database()
            # Convert product id from string to ObjectId (MongoDB as another no-relational databases uses a different ID type)
            try:
                obj_id = ObjectId(product_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid ObjectID format")
            product = await db["products"].find_one({"_id": obj_id}) # MongoDB query using ObjectId
            
            print(f"Fetching data from Database: {product}")
            # Save on cache with Redis
            if product:
                # Save on cache the retrieved data from the database
                save_hash(product_id, product)
                data = product
            else:
                raise HTTPException(status_code=404, detail="Product not found")
        return Product(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")    

        
@router.post("/products/", response_model=Product)
async def create_product(product: Product):
    """
    Creates a new product.

    This endpoint checks if the provided product already exists in the MongoDB database 
    by matching its `name` and `country` fields. If the product exists, it skips saving 
    and directly returns the existing product's data. If it does not exist, the product is saved 
    to the database and cached in Redis for future queries.

    Process:
    1. Verify if the product exists in the database:
        - If found: Return the existing product data.
        - If not found: Save the new product to the database.
    2. After saving, retrieve the saved document, transform its `_id` for JSON compatibility, and cache the data in Redis.
    3. Return the newly saved product data.

    Args:
        product (Product): A Pydantic model representing the product object, containing fields like `name` and `country`.

    Returns:
        dict: The product's data either from the database or from the newly inserted document.

    Raises:
        HTTPException: 
            - 404: If the product could not be found after insertion.
            - 500: If there was an issue saving the product or another unexpected error occurred.
    """
    db = await get_database()

    existing_product = await db["products"].find_one({"name":product.name, "country":product.country}) # Find one requires a filter dictionary, for example {"key":"value"} to search for the item that matches it, not an object or complete dictionary instead.
    print(existing_product)
    if existing_product:
        print(f"{existing_product} This object already exists in database.")
        return existing_product
    else:
        try:
            # Save on database with MongoDB
            result = await db["products"].insert_one(product.model_dump())
            print("Data saved on DB: {}".format(result))
            
            if result.acknowledged:
                # Fetch saved object from MongoDB
                fetched_product = await db["products"].find_one({"_id": result.inserted_id})
                
                if fetched_product:
                    # Transform MongoDB `_id` to string for JSON compatibility
                    fetched_product["_id"] = str(fetched_product["_id"])

                    # Save on cache with Redis
                    save_hash(key=fetched_product["_id"], data=fetched_product)

                    # Return the fetched document
                    return fetched_product
                else:
                    raise HTTPException(status_code=404, detail="Product not found after insertion")
            else:
                raise HTTPException(status_code=500, detail="Product not created")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {e}")