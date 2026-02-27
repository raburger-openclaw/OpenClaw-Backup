"""
VA QC App - Phase 1: Foundation
FastAPI web app for valve tracking
"""
from fastapi import FastAPI, Request, Form, HTTPException, Depends, status, UploadFile, File
from pathlib import Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import bcrypt
import os
from typing import Optional

from config import SECRET_KEY, USERS, APP_NAME, ARTISANS, STATUSES
from google_sheets import ValveDataStore

app = FastAPI(title=APP_NAME, version="1.0.0")

# Session middleware for login
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=3600 * 8  # 8 hours
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session"""
    user = request.session.get("user")
    if user:
        return user
    return None

def require_login(request: Request):
    """Dependency to require login"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root - redirect to login or dashboard"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
        "app_name": APP_NAME
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    user = USERS.get(username.lower())
    
    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password",
            "app_name": APP_NAME
        })
    
    request.session["user"] = {
        "username": username.lower(),
        "name": user["name"],
        "role": user["role"],
        "email": user["email"]
    }
    
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_login)):
    """Main dashboard - valve list"""
    try:
        store = ValveDataStore()
        valves = store.get_all_valves()
        error_msg = None
    except Exception as e:
        valves = []
        error_msg = str(e)
    
    in_progress = [v for v in valves if v.get('Status', '') in ['Received', 'In Stripped', 'In Before Assembly', 'In Final']]
    complete = [v for v in valves if v.get('Status', '') == 'Complete']
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "valves": valves,
        "in_progress_count": len(in_progress),
        "complete_count": len(complete),
        "app_name": APP_NAME,
        "error": error_msg
    })

@app.get("/valve/new", response_class=HTMLResponse)
async def new_valve_form(request: Request, user: dict = Depends(require_login)):
    """Show new valve form"""
    return templates.TemplateResponse("valve_form.html", {
        "request": request,
        "user": user,
        "app_name": APP_NAME,
        "artisans": ARTISANS,
        "statuses": STATUSES
    })

@app.post("/valve/new")
async def create_valve(
    request: Request,
    qj_number: str = Form(...),
    wg_number: str = Form(...),
    size: str = Form(...),
    body_brand: str = Form(...),
    body_type: str = Form(...),
    actuator_brand: str = Form(...),
    actuator_type: str = Form(...),
    model_number: str = Form(""),
    artisan: str = Form(...),
    notes: str = Form(""),
    user: dict = Depends(require_login)
):
    """Create new valve"""
    try:
        store = ValveDataStore()
        valve_data = {
            "QJ Number": qj_number,
            "WG Number": wg_number,
            "Date Received": datetime.now().strftime("%Y-%m-%d"),
            "Status": "Received",
            "Artisan": artisan,
            "Size": size,
            "Body Brand": body_brand,
            "Body Type": body_type,
            "Actuator Brand": actuator_brand,
            "Actuator Type": actuator_type,
            "Model Number": model_number,
            "Notes": notes,
            "Email Sent": ""
        }
        success = store.create_valve(valve_data)
        if not success:
            return templates.TemplateResponse("valve_form.html", {
                "request": request,
                "user": user,
                "app_name": APP_NAME,
                "artisans": ARTISANS,
                "statuses": STATUSES,
                "error": "Failed to save valve to spreadsheet."
            })
        return RedirectResponse(url="/dashboard", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("valve_form.html", {
            "request": request,
            "user": user,
            "app_name": APP_NAME,
            "artisans": ARTISANS,
            "statuses": STATUSES,
            "error": f"Error: {str(e)}"
        })

@app.get("/valve/{job_number}", response_class=HTMLResponse)
async def valve_detail(request: Request, job_number: str, user: dict = Depends(require_login)):
    """Single valve detail view"""
    try:
        store = ValveDataStore()
        valves = store.get_all_valves()
        valve = next((v for v in valves if v.get("Job Number") == job_number), None)
    except Exception as e:
        valve = None
    
    return templates.TemplateResponse("valve_detail.html", {
        "request": request,
        "user": user,
        "valve": valve,
        "job_number": job_number,
        "app_name": APP_NAME
    })

@app.get("/valve/{job_number}/edit", response_class=HTMLResponse)
async def edit_valve_form(request: Request, job_number: str, user: dict = Depends(require_login)):
    """Show edit valve form"""
    try:
        store = ValveDataStore()
        valve = store.get_valve_by_job(job_number)
    except Exception as e:
        valve = None
    
    return templates.TemplateResponse("valve_edit.html", {
        "request": request,
        "user": user,
        "valve": valve,
        "job_number": job_number,
        "app_name": APP_NAME,
        "artisans": ARTISANS,
        "statuses": STATUSES
    })

@app.post("/valve/{job_number}/edit")
async def update_valve(
    request: Request,
    job_number: str,
    body_brand: str = Form(...),
    body_type: str = Form(...),
    actuator_brand: str = Form(...),
    actuator_type: str = Form(...),
    model_number: str = Form(""),
    size: str = Form(...),
    artisan: str = Form(...),
    status: str = Form(...),
    notes: str = Form(""),
    user: dict = Depends(require_login)
):
    """Update existing valve"""
    try:
        store = ValveDataStore()
        valve_data = {
            "Body Brand": body_brand,
            "Body Type": body_type,
            "Actuator Brand": actuator_brand,
            "Actuator Type": actuator_type,
            "Model Number": model_number,
            "Size": size,
            "Artisan": artisan,
            "Status": status,
            "Notes": notes
        }
        success = store.update_valve(job_number, valve_data)
        if not success:
            return templates.TemplateResponse("valve_edit.html", {
                "request": request,
                "user": user,
                "valve": store.get_valve_by_job(job_number),
                "job_number": job_number,
                "app_name": APP_NAME,
                "artisans": ARTISANS,
                "statuses": STATUSES,
                "error": "Failed to update valve."
            })
        return RedirectResponse(url=f"/valve/{job_number}", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("valve_edit.html", {
            "request": request,
            "user": user,
            "valve": None,
            "job_number": job_number,
            "app_name": APP_NAME,
            "artisans": ARTISANS,
            "statuses": STATUSES,
            "error": f"Error: {str(e)}"
        })

@app.get("/valve/{job_number}/receiving", response_class=HTMLResponse)
async def receiving_form(request: Request, job_number: str, user: dict = Depends(require_login)):
    """Show receiving form for valve"""
    try:
        store = ValveDataStore()
        valve = store.get_valve_by_job(job_number)
        receiving = store.get_receiving_by_job(job_number)
    except Exception as e:
        valve = None
        receiving = None
    
    return templates.TemplateResponse("receiving_form.html", {
        "request": request,
        "user": user,
        "valve": valve,
        "job_number": job_number,
        "receiving": receiving,
        "app_name": APP_NAME
    })

@app.post("/valve/{job_number}/receiving")
async def save_receiving(
    request: Request,
    job_number: str,
    notes: str = Form(""),
    action: str = Form("save"),
    manager_notes: str = Form(""),
    photo_1: UploadFile = File(None),
    photo_2: UploadFile = File(None),
    photo_3: UploadFile = File(None),
    photo_4: UploadFile = File(None),
    photo_5: UploadFile = File(None),
    photo_6: UploadFile = File(None),
    photo_7: UploadFile = File(None),
    photo_8: UploadFile = File(None),
    photo_9: UploadFile = File(None),
    photo_10: UploadFile = File(None),
    user: dict = Depends(require_login)
):
    """Save receiving data with photo uploads or handle manager approval"""
    try:
        from google_drive import GoogleDriveClient
        import uuid
        
        store = ValveDataStore()
        drive = GoogleDriveClient()
        
        photos = [photo_1, photo_2, photo_3, photo_4, photo_5, 
                  photo_6, photo_7, photo_8, photo_9, photo_10]
        
        # Handle file uploads for all users (capture photos)
        photo_urls = {}
        upload_dir = Path("/app/static/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for i, photo in enumerate(photos, 1):
            if photo and photo.filename:
                # Save temp file
                temp_path = upload_dir / f"{uuid.uuid4()}_{photo.filename}"
                with open(temp_path, "wb") as f:
                    content = await photo.read()
                    f.write(content)
                
                # Upload to Google Drive
                file_name = f"Receiving_{i}_{photo.filename}"
                drive_url = drive.upload_photo(
                    str(temp_path), 
                    file_name, 
                    job_number, 
                    "Receiving"
                )
                
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
                
                if drive_url:
                    photo_urls[f"Photo {i}"] = drive_url
        
        # Save to receiving sheet
        receiving_data = {
            "Job Number": job_number,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Artisan": user["name"],
            "Notes": notes,
            "Complete": "false",
            "Approved": "false",
            **photo_urls
        }
        
        # If manager approval action
        if action == "approve" and user["role"] in ["manager", "admin"]:
            receiving_data["Approved"] = "true"
            receiving_data["Complete"] = "true"
            receiving_data["Manager Notes"] = manager_notes
            success = store.save_receiving(receiving_data)
            if success:
                store.update_valve_status(job_number, "In Stripped")
                return RedirectResponse(url=f"/valve/{job_number}", status_code=302)
        elif action == "reject" and user["role"] in ["manager", "admin"]:
            receiving_data["Approved"] = "false"
            receiving_data["Complete"] = "false"
            receiving_data["Manager Notes"] = manager_notes
            success = store.save_receiving(receiving_data)
            if success:
                return RedirectResponse(url=f"/valve/{job_number}", status_code=302)
        else:
            # Regular save by artisan or manager
            success = store.save_receiving(receiving_data)
            if success:
                return RedirectResponse(url=f"/valve/{job_number}", status_code=302)
        
        return templates.TemplateResponse("receiving_form.html", {
            "request": request,
            "user": user,
            "job_number": job_number,
            "error": "Failed to save data"
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR in save_receiving: {e}")
        print(traceback.format_exc())
        return templates.TemplateResponse("receiving_form.html", {
            "request": request,
            "user": user,
            "job_number": job_number,
            "error": f"Error: {str(e)}"
        })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0", "phase": 2}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)