#!/usr/bin/env python3
"""Find the shared folder ID for VA QC Photos"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('drive', 'v3', credentials=creds)

print("Searching for shared folders...")
results = service.files().list(
    q="mimeType='application/vnd.google-apps.folder' and trashed=false",
    spaces='drive',
    fields='files(id, name, shared, owners)'
).execute()

files = results.get('files', [])
print(f"\nFound {len(files)} folders accessible to service account:\n")

for f in files:
    print(f"Name: {f.get('name')}")
    print(f"ID: {f.get('id')}")
    print(f"Shared: {f.get('shared', False)}")
    print("-" * 50)
