# CSV Data Cleaning Tool

A full-stack CSV data cleaning web application.

## Architecture
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: MongoDB (Atlas or Local)

## Features
- CSV upload and preview
- Automatic data cleaning
- Column-level operations
- Data quality report
- Cleaning history storage
- Download cleaned CSV

## How to Run Locally

1. Ensure you have Python installed.
2. Run the application script:

```bash
python run_app.py
```

This script will:
- Install necessary dependencies from `requirements.txt`.
- Start the FastAPI backend server (http://localhost:8000).
- Start the Streamlit frontend (http://localhost:8501).
- Open the application in your browser.
