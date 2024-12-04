from motor.motor_asyncio import AsyncIOMotorClient
import os 

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClien(MONGO_URI)

async def get_database():
    return client.ProductsDB