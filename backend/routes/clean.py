from fastapi import APIRouter, HTTPException
import pandas as pd
import os

from backend.services.cleaner import auto_clean
from backend.services.stats import data_quality_report
from backend.database.mongodb import history_collection

router = APIRouter()

from backend.config import UPLOAD_DIR, CLEANED_DIR
import traceback

@router.post("/auto-clean")
def auto_clean_file(file_id: str):
    try:
        print(f"DEBUG: Processing file_id={file_id}")
        input_path = os.path.join(UPLOAD_DIR, file_id)
        print(f"DEBUG: Input path={input_path}")

        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="File not found")

        df = pd.read_csv(input_path)

        df_cleaned, actions = auto_clean(df)
        report = data_quality_report(df_cleaned)

        output_path = os.path.join(CLEANED_DIR, file_id)
        df_cleaned.to_csv(output_path, index=False)

        history_collection.insert_one({
            "filename": file_id,
            "rows": len(df_cleaned),
            "columns": list(df_cleaned.columns),
            "actions": actions
        })

        return {
            "status": "success",
            "actions": actions,
            "report": report
        }

    except Exception as e:
        print("ERROR DETAILS:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
