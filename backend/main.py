from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import upload, clean, history, rename
from backend.config import DATA_DIR
import os

from fastapi.responses import RedirectResponse

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return RedirectResponse(url="/history")

# Mount data directory for downloads
# Ensure directory exists first (config.py handles it, but good to be safe)
os.makedirs(DATA_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=DATA_DIR), name="files")

app.include_router(upload.router)
app.include_router(clean.router)
app.include_router(history.router)
app.include_router(rename.router)
