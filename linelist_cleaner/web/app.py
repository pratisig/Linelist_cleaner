"""
FastAPI Main Application and Static Server.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from linelist_cleaner.web.api import router as api_router
from linelist_cleaner.utils import get_resource_path

# Resolve static directory for both local dev and PyInstaller frozen executable
STATIC_DIR = get_resource_path(os.path.join("linelist_cleaner", "web", "static"))
if not os.path.exists(STATIC_DIR):
    # Fallback to local relative path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Linelist Cleaner",
    description="Epidemiological Linelist Data Cleaning, Validation, and Spatial Cascade Engine",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount static files if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the main application Single Page Interface."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Linelist Cleaner API is active. Open /docs for API documentation."}
