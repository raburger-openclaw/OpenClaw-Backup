"""
Local photo storage for VA QC App
Photos saved to static/uploads/{job_number}/{stage}/
"""
import os
from pathlib import Path
from typing import Optional
import shutil

# Base upload directory
UPLOAD_DIR = Path("/app/static/uploads")

def get_valve_photo_dir(job_number: str, stage: str) -> Path:
    """Get the directory for valve photos"""
    return UPLOAD_DIR / job_number.replace("/", "_") / stage.replace(" ", "_")

def ensure_upload_dir():
    """Ensure base upload directory exists"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_photo(file_content: bytes, file_name: str, job_number: str, stage: str) -> Optional[str]:
    """Save photo to local storage and return the URL path"""
    try:
        ensure_upload_dir()
        
        # Create valve stage directory
        photo_dir = get_valve_photo_dir(job_number, stage)
        photo_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean filename
        clean_name = file_name.replace(" ", "_")
        file_path = photo_dir / clean_name
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Return URL path (relative for templates)
        job_clean = job_number.replace("/", "_")
        stage_clean = stage.replace(" ", "_")
        return f"/static/uploads/{job_clean}/{stage_clean}/{clean_name}"
        
    except Exception as e:
        print(f"ERROR saving photo: {e}")
        return None

def get_photo_urls(job_number: str, stage: str) -> list:
    """Get all photo URLs for a valve stage"""
    try:
        photo_dir = get_valve_photo_dir(job_number, stage)
        if not photo_dir.exists():
            return []
        
        job_clean = job_number.replace("/", "_")
        stage_clean = stage.replace(" ", "_")
        
        urls = []
        for f in sorted(photo_dir.iterdir()):
            if f.is_file():
                urls.append(f"/static/uploads/{job_clean}/{stage_clean}/{f.name}")
        return urls
        
    except Exception as e:
        print(f"ERROR getting photos: {e}")
        return []

def delete_photo(job_number: str, stage: str, file_name: str) -> bool:
    """Delete a specific photo"""
    try:
        photo_path = get_valve_photo_dir(job_number, stage) / file_name
        if photo_path.exists():
            photo_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"ERROR deleting photo: {e}")
        return False
