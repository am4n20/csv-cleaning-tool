from datetime import datetime

def cleaning_history_model(
    filename: str,
    rows: int,
    columns: list,
    actions: list
):
    return {
        "filename": filename,
        "rows": rows,
        "columns": columns,
        "actions_taken": actions,
        "timestamp": datetime.now()
    }
