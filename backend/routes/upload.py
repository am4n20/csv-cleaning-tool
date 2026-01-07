from fastapi import APIRouter, UploadFile
import pandas as pd
import uuid, os

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_csv(file: UploadFile):
    file_id = f"{uuid.uuid4()}.csv"
    path = os.path.join(UPLOAD_DIR, file_id)

    with open(path, "wb") as f:
        f.write(await file.read())

    df = pd.read_csv(path)
    return {
        "file_id": file_id,
        "columns": df.columns.tolist(),
        "preview": df.head(5).to_dict()
    }
