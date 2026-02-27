"""
VA QC App Configuration
No paid services - all free/OSS only
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# App Settings
APP_NAME = "VA QC - Valve Tracking"
APP_VERSION = "2.0.0"

# Domain (for emails/links)
DOMAIN = "vulcanarc.co.za"
APP_URL = f"https://qc.{DOMAIN}"

# Google Sheets
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SPREADSHEET_NAME = "VA QC V2 - Valve Tracking"

# Google Drive
GOOGLE_DRIVE_FOLDER = "VulcanArc/ValveQC"

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "vulcan-qc-dev-key-change-in-production")
SESSION_TIMEOUT_HOURS = 8

# Users (password: vulcan123)
USERS = {
    "rob": {
        "password": "$2b$12$vPGlmvC/QuMm6XKHJ/LC.O5BTeb/lyUllkTiAYMoyiuXgKsNRDeim",
        "role": "admin",
        "email": "rob@vulcanarc.co.za",
        "name": "Robert Burger"
    },
    "gideon": {
        "password": "$2b$12$vPGlmvC/QuMm6XKHJ/LC.O5BTeb/lyUllkTiAYMoyiuXgKsNRDeim",
        "role": "manager",
        "email": "gideon@vulcanarc.co.za",
        "name": "Gideon"
    },
    "lerato": {
        "password": "$2b$12$vPGlmvC/QuMm6XKHJ/LC.O5BTeb/lyUllkTiAYMoyiuXgKsNRDeim",
        "role": "artisan",
        "email": "lerato@vulcanarc.co.za",
        "name": "Lerato"
    },
    "demo": {
        "password": "$2b$12$vPGlmvC/QuMm6XKHJ/LC.O5BTeb/lyUllkTiAYMoyiuXgKsNRDeim",
        "role": "client",
        "email": "client@demo.com",
        "name": "Demo Client"
    }
}

# Email settings
EMAIL_ENABLED = True
EMAIL_SMTP = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER", "robertburgerbot@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Notifications
NOTIFY_ON_STAGE_COMPLETE = True
NOTIFY_ON_VALVE_COMPLETE = True

# File upload
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_IMAGE_TYPES = {".jpg", ".jpeg", ".png"}

# Artisan list
ARTISANS = ["Lerato", "Maxon", "Thabo", "Gideon", "Annerien", "RJ", "Anton"]

# Valve statuses
STATUSES = [
    "Received",
    "In Stripped", 
    "In Before Assembly",
    "In Final",
    "Complete"
]