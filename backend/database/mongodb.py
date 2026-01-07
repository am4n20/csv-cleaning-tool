from pymongo import MongoClient
from backend.config import MONGO_URL, DB_NAME

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
history_collection = db["cleaning_history"]
