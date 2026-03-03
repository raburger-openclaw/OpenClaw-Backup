"""
Google Drive integration for photo uploads
Uses Service Account authentication
"""
import os
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# OAuth scopes - need Drive file scope for uploads
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')

# Shared folder for all valve photos in Drive
# This folder must be created in YOUR Drive and shared with the service account
PARENT_FOLDER_NAME = "VulcanArc ValveQC Photos"

# If you have the shared folder ID, set it here:
# Folder ID for "VA QC V2 - Valve Tracking - Photos" (shared with service account)
SHARED_FOLDER_ID = os.getenv("SHARED_FOLDER_ID", "1XZ0qLeiMwZgnpydaMN2WTtbaw-6R_ebc")


class GoogleDriveClient:
    """Client for Google Drive API using Service Account"""
    
    def __init__(self):
        self.service = None
        self.parent_folder_id = None
        self._authenticate()
        self._ensure_parent_folder()
    
    def _authenticate(self):
        """Authenticate with Google"""
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise Exception(f"Service account key not found at {SERVICE_ACCOUNT_FILE}")
        
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _ensure_parent_folder(self):
        """Find the shared ValveQC folder (must be shared with service account)"""
        try:
            # Option 1: Use explicit folder ID from env
            if SHARED_FOLDER_ID:
                self.parent_folder_id = SHARED_FOLDER_ID
                print(f"Using shared folder ID from config: {SHARED_FOLDER_ID}")
                return
            
            # Option 2: Search for folder shared with service account
            # Service accounts can access files shared with them
            results = self.service.files().list(
                q=f"name='{PARENT_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name, shared, owners)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                self.parent_folder_id = files[0]['id']
                print(f"Found shared folder: {PARENT_FOLDER_NAME} ({self.parent_folder_id})")
            else:
                # Can't create - service account has no storage
                print(f"ERROR: Shared folder '{PARENT_FOLDER_NAME}' not found!")
                print(f"Create this folder in YOUR Google Drive and share it with:")
                print(f"  va-qc-app@va-qc-app.iam.gserviceaccount.com")
                print(f"Or set SHARED_FOLDER_ID environment variable")
                self.parent_folder_id = None
                
        except Exception as e:
            print(f"ERROR ensuring parent folder: {e}")
            self.parent_folder_id = None
    
    def get_or_create_valve_folder(self, job_number: str) -> Optional[str]:
        """Get or create a folder for a specific valve"""
        if not self.parent_folder_id:
            return None
        
        try:
            folder_name = f"{job_number}"
            
            # Search for existing
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{self.parent_folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']
            
            # Create folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.parent_folder_id]
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            return folder['id']
            
        except Exception as e:
            print(f"ERROR creating valve folder: {e}")
            return None
    
    def upload_photo(self, file_path: str, file_name: str, job_number: str, stage: str) -> Optional[str]:
        """Upload a photo to Drive and return the direct URL"""
        try:
            # Get/create valve folder
            valve_folder_id = self.get_or_create_valve_folder(job_number)
            if not valve_folder_id:
                print("ERROR: Could not get valve folder")
                return None
            
            # Create stage subfolder
            stage_folder_name = stage.replace(" ", "_")
            
            # Check if stage folder exists
            results = self.service.files().list(
                q=f"name='{stage_folder_name}' and mimeType='application/vnd.google-apps.folder' and '{valve_folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                stage_folder_id = files[0]['id']
            else:
                # Create stage folder
                folder_metadata = {
                    'name': stage_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [valve_folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                stage_folder_id = folder['id']
            
            # Upload file
            file_metadata = {
                'name': file_name,
                'parents': [stage_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            # Make file publicly viewable (anyone with link)
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file['id'],
                body=permission
            ).execute()
            
            # Return direct image link
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
            
        except Exception as e:
            print(f"ERROR uploading photo: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"ERROR deleting file: {e}")
            return False
