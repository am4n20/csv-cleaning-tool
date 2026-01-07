from fastapi import APIRouter, HTTPException, Body
import pandas as pd
import os
from backend.config import UPLOAD_DIR

router = APIRouter()

@router.post("/rename")
def rename_columns(
    file_id: str = Body(...),
    columns: dict = Body(...)
):
    try:
        input_path = os.path.join(UPLOAD_DIR, file_id)
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="File not found")

        df = pd.read_csv(input_path)
        
        # Rename columns
        df.rename(columns=columns, inplace=True)
        
        # Save back to the same file
        df.to_csv(input_path, index=False)

        return {
            "status": "success",
            "message": "Columns renamed successfully",
            "columns": df.columns.tolist(),
            "preview": df.head(5).to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
