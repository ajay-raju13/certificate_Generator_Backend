from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import uuid
from typing import Dict
import os
import time
import asyncio
from contextlib import asynccontextmanager

from .config import (
    TEMPLATES_DIR, OUTPUT_DIR, TEMP_DIR, FONTS_DIR,
    TEMPLATE_FILENAME, EXCEL_FILENAME
)

from .utils.excel_reader import read_excel_rows
from .utils.image_processor import render_certificate_image, pil_image_to_bytes
from .utils.pdf_generator import create_pdfs_from_rows, zip_files
from .utils.storage_manager import StorageManager

# Initialize storage manager (Retention: 24 hours)
storage_manager = StorageManager(OUTPUT_DIR, TEMP_DIR, TEMPLATES_DIR, retention_hours=24)

async def scheduled_cleanup_task():
    """Background task to clean up old files every hour"""
    while True:
        try:
            print(f"[Scheduler] Running hourly cleanup check...")
            stats = storage_manager.full_cleanup()
            if sum(stats.values()) > 0:
                print(f"[Scheduler] Cleanup stats: {stats}")
        except Exception as e:
            print(f"[Scheduler] Error during cleanup: {e}")
        
        # Wait for 1 hour (3600 seconds)
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background task
    task = asyncio.create_task(scheduled_cleanup_task())
    yield
    # Shutdown: Cancel task if needed (optional, simplistic handling here)
    task.cancel()

app = FastAPI(title="Certificate Generator Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve static directory
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")



# in-memory store (simple)
CURRENT = {
    "template_path": None,
    "excel_path": None,
    "placeholders": {},
    "default_font": None,
    "filename_field": None
}

def save_upload(file: UploadFile, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest

@app.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(400, "Template must be PNG or JPG")
    dest = TEMPLATES_DIR / TEMPLATE_FILENAME
    save_upload(file, dest)
    CURRENT["template_path"] = dest
    return {"status": "ok", "template": dest.name}

@app.get("/template")
def get_template():
    tpl = CURRENT.get("template_path")
    if not tpl or not tpl.exists():
        return {"url": None}
    return {"url": f"http://127.0.0.1:8000/static/templates/{tpl.name}"}

@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".xlsx", ".xls"}:
        raise HTTPException(400, "Excel must be XLSX or XLS")
    dest = TEMP_DIR / EXCEL_FILENAME
    save_upload(file, dest)
    CURRENT["excel_path"] = dest
    return {"status": "ok", "excel": dest.name}

@app.get("/excel-headers")
async def get_excel_headers():
    excel = CURRENT.get("excel_path")
    if not excel or not excel.exists():
        raise HTTPException(400, "Excel not uploaded")
    try:
        from .utils.excel_reader import get_excel_headers as get_headers
        headers = get_headers(excel)
        return {"headers": headers}
    except Exception as e:
        raise HTTPException(400, f"Error reading headers: {str(e)}")

@app.post("/set-placeholders")
async def set_placeholders(payload: Dict):
    placeholders = payload.get("placeholders")
    default_font = payload.get("default_font")
    filename_field = payload.get("filename_field")
    
    if not isinstance(placeholders, dict):
        raise HTTPException(400, "placeholders must be a dictionary")
    
    # validate x,y,width,height exist
    for key, v in placeholders.items():
        if "x" not in v or "y" not in v or "width" not in v or "height" not in v:
            raise HTTPException(400, f"Placeholder '{key}' missing x/y/width/height")
    
    CURRENT["placeholders"] = placeholders
    CURRENT["default_font"] = default_font
    CURRENT["filename_field"] = filename_field
    return {"status": "ok"}

@app.post("/preview")
async def preview_image(row_index: int = Form(0)):
    tpl = CURRENT["template_path"]
    excel = CURRENT["excel_path"]
    placeholders = CURRENT["placeholders"]
    if not tpl or not tpl.exists():
        raise HTTPException(400, "Template not uploaded")
    if not excel or not excel.exists():
        raise HTTPException(400, "Excel not uploaded")
    rows = read_excel_rows(excel)
    if row_index < 0 or row_index >= len(rows):
        raise HTTPException(400, "row_index out of bounds")
    row = rows[row_index]
    img = render_certificate_image(tpl, placeholders, row, FONTS_DIR, CURRENT.get("default_font"))
    data = pil_image_to_bytes(img, format="PNG")
    return StreamingResponse(iter([data]), media_type="image/png")

@app.post("/generate")
async def generate_all(folder_name: str = Form(None)):
    tpl = CURRENT["template_path"]
    excel = CURRENT["excel_path"]
    placeholders = CURRENT["placeholders"]
    filename_field = CURRENT.get("filename_field")
    
    if not tpl or not tpl.exists():
        raise HTTPException(400, "Template not uploaded")
    if not excel or not excel.exists():
        raise HTTPException(400, "Excel not uploaded")
    rows = read_excel_rows(excel)
    if len(rows) == 0:
        raise HTTPException(400, "No rows found in excel")
    job_id = folder_name or str(uuid.uuid4())
    job_folder = OUTPUT_DIR / job_id
    job_folder.mkdir(parents=True, exist_ok=True)
    pdf_paths = create_pdfs_from_rows(tpl, rows, placeholders, FONTS_DIR, job_folder, CURRENT.get("default_font"), filename_field)
    zip_path = OUTPUT_DIR / f"{job_id}.zip"
    zip_files(pdf_paths, zip_path)
    

    

    

    
    # Files are kept for preview (cleaned up by background scheduler after 24h)
    file_list = [p.name for p in pdf_paths]
    
    return {
        "status": "ok", 
        "zip": zip_path.name, 
        "count": len(pdf_paths),
        "job_id": job_id,
        "files": file_list
    }

@app.get("/download/{zip_name}")
async def download_zip(zip_name: str):
    zip_path = OUTPUT_DIR / zip_name
    if not zip_path.exists():
        raise HTTPException(404, "Zip file not found")
    return FileResponse(zip_path, filename=zip_name, media_type="application/zip")



@app.get("/storage-info")
async def storage_info():
    """Get current storage usage information"""
    info = storage_manager.get_storage_info()
    return {
        "status": "ok",
        "storage": info,
        "message": f"Total storage used: {info['total_mb']} MB"
    }

@app.post("/storage-cleanup")
async def storage_cleanup():
    """Trigger full storage cleanup"""
    stats = storage_manager.full_cleanup(force=True)
    return {
        "status": "ok",
        "cleanup_stats": stats,
        "storage_after": storage_manager.get_storage_info()
    }

@app.get("/status")
def status():
    return {
        "template": str(CURRENT.get("template_path").name) if CURRENT.get("template_path") else None,
        "excel": str(CURRENT.get("excel_path").name) if CURRENT.get("excel_path") else None,
        "placeholders": CURRENT.get("placeholders"),
        "default_font": CURRENT.get("default_font"),
        "filename_field": CURRENT.get("filename_field")
    }
