from fastapi import APIRouter
from backend.database.mongodb import history_collection

router = APIRouter()

@router.get("/history")
def get_history():
    records = list(history_collection.find({}, {"_id": 0}))
    return records
