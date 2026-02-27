"""
Google Sheets integration for VA QC App
Uses Service Account authentication
"""
import os
from typing import List, Dict, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Service account key file
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')

# HARDCODED SPREADSHEET ID - Rob's VA QC Sheet
# https://docs.google.com/spreadsheets/d/12GKd7Wv78KYQBvfPe_GfO2E9dJN6QMGM8hziWWqEq6A/edit
DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "12GKd7Wv78KYQBvfPe_GfO2E9dJN6QMGM8hziWWqEq6A")


class GoogleSheetsClient:
    """Client for Google Sheets API using Service Account"""
    
    def __init__(self, spreadsheet_id: str = None):
        self.service = None
        self.spreadsheet_id = spreadsheet_id or DEFAULT_SPREADSHEET_ID
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google using Service Account"""
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise Exception(f"Service account key not found at {SERVICE_ACCOUNT_FILE}")
        
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        
        self.service = build('sheets', 'v4', credentials=creds)
    
    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Read data from sheet range"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            print(f"Error reading sheet: {e}")
            return []
    
    def append_row(self, spreadsheet_id: str, range_name: str, values: List[Any]) -> bool:
        """Append row to sheet"""
        try:
            body = {'values': [values]}
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            return True
        except HttpError as e:
            print(f"Error appending row: {e}")
            return False
    
    def update_row(self, spreadsheet_id: str, range_name: str, values: List[Any]) -> bool:
        """Update a row in sheet"""
        try:
            body = {'values': [values]}
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            return True
        except HttpError as e:
            print(f"Error updating row: {e}")
            return False
    
    def get_headers(self, spreadsheet_id: str, sheet_name: str) -> List[str]:
        """Get column headers from sheet"""
        data = self.read_sheet(spreadsheet_id, f"{sheet_name}!A1:Z1")
        return data[0] if data else []


class ValveDataStore:
    """High-level interface for valve data"""
    
    def __init__(self):
        self.client = GoogleSheetsClient()
    
    def get_all_valves(self) -> List[Dict]:
        """Get all valve records"""
        if not self.client.spreadsheet_id:
            print("WARNING: No SPREADSHEET_ID set")
            return []
        
        headers = self.client.read_sheet(self.client.spreadsheet_id, "Valves!A1:Z1")
        headers = headers[0] if headers else []
        
        data = self.client.read_sheet(self.client.spreadsheet_id, "Valves!A2:Z1000")
        
        valves = []
        for i, row in enumerate(data):
            if not row or not row[0]:  # Skip empty rows
                continue
            valve = {"_row_index": i + 2}  # +2 because row 1 is headers
            for j, header in enumerate(headers):
                valve[header] = row[j] if j < len(row) else ""
            valves.append(valve)
        
        return valves
    
    def get_valve_by_job(self, job_number: str) -> Optional[Dict]:
        """Get valve by job number"""
        valves = self.get_all_valves()
        for valve in valves:
            if valve.get("Job Number") == job_number:
                return valve
        return None
    
    def create_valve(self, valve_data: Dict) -> bool:
        """Create new valve record in Valves sheet"""
        try:
            headers = self.client.get_headers(self.client.spreadsheet_id, "Valves")
            if not headers:
                print("ERROR: Could not get headers from Valves sheet")
                return False
            
            # Build row based on headers
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")  # System column
                elif header == "Job Number":
                    # Compute job number from QJ and WG
                    qj = valve_data.get("QJ Number", "")
                    wg = valve_data.get("WG Number", "")
                    row.append(f"{qj}-{wg}" if qj and wg else "")
                else:
                    row.append(valve_data.get(header, ""))
            
            return self.client.append_row(self.client.spreadsheet_id, "Valves!A1", row)
        except Exception as e:
            print(f"ERROR creating valve: {e}")
            return False
    
    def update_valve(self, job_number: str, valve_data: Dict) -> bool:
        """Update existing valve in Valves sheet"""
        try:
            # Find the valve first
            valve = self.get_valve_by_job(job_number)
            if not valve:
                print(f"ERROR: Valve {job_number} not found")
                return False
            
            row_index = valve.get("_row_index")
            if not row_index:
                print(f"ERROR: Could not determine row for {job_number}")
                return False
            
            headers = self.client.get_headers(self.client.spreadsheet_id, "Valves")
            if not headers:
                print("ERROR: Could not get headers from Valves sheet")
                return False
            
            # Build row based on headers
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")  # System column
                elif header == "Job Number":
                    # Keep original job number
                    row.append(job_number)
                else:
                    row.append(valve_data.get(header, valve.get(header, "")))
            
            # Update the row
            range_name = f"Valves!A{row_index}:Z{row_index}"
            return self.client.update_row(self.client.spreadsheet_id, range_name, row)
            
        except Exception as e:
            print(f"ERROR updating valve: {e}")
            return False
    
    def update_valve_status(self, job_number: str, status: str) -> bool:
        """Update just the status of a valve"""
        try:
            valve = self.get_valve_by_job(job_number)
            if not valve:
                return False
            
            headers = self.client.get_headers(self.client.spreadsheet_id, "Valves")
            if not headers:
                return False
            
            # Find Status column index
            try:
                status_col_idx = headers.index("Status")
            except ValueError:
                print("ERROR: Status column not found")
                return False
            
            # Convert to column letter (A=0, B=1, etc.)
            col_letter = chr(65 + status_col_idx)  # A=65 in ASCII
            
            row_index = valve.get("_row_index")
            range_name = f"Valves!{col_letter}{row_index}"
            
            return self.client.update_row(
                self.client.spreadsheet_id, 
                range_name, 
                [status]
            )
        except Exception as e:
            print(f"ERROR updating valve status: {e}")
            return False
    
    def get_receiving_by_job(self, job_number: str) -> Optional[Dict]:
        """Get receiving record for a valve"""
        try:
            headers = self.client.read_sheet(self.client.spreadsheet_id, "Receiving!A1:Z1")
            headers = headers[0] if headers else []
            
            data = self.client.read_sheet(self.client.spreadsheet_id, "Receiving!A2:Z1000")
            
            for i, row in enumerate(data):
                if not row or len(row) < 1:
                    continue
                
                # Check if this is the right job
                job_col_idx = headers.index("Job Number") if "Job Number" in headers else 2
                if len(row) > job_col_idx and row[job_col_idx] == job_number:
                    receiving = {"_row_index": i + 2}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            receiving[header] = row[j]
                        else:
                            receiving[header] = ""
                    return receiving
            
            return None
            
        except Exception as e:
            print(f"ERROR getting receiving: {e}")
            return None
    
    def save_receiving(self, receiving_data: Dict) -> bool:
        """Save receiving record"""
        try:
            # Check if already exists
            existing = self.get_receiving_by_job(receiving_data.get("Job Number"))
            
            headers = self.client.get_headers(self.client.spreadsheet_id, "Receiving")
            if not headers:
                print("ERROR: Could not get headers from Receiving sheet")
                return False
            
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")
                else:
                    row.append(receiving_data.get(header, ""))
            
            if existing:
                # Update existing
                row_index = existing.get("_row_index")
                range_name = f"Receiving!A{row_index}:Z{row_index}"
                return self.client.update_row(self.client.spreadsheet_id, range_name, row)
            else:
                # Create new
                return self.client.append_row(self.client.spreadsheet_id, "Receiving!A1", row)
                
        except Exception as e:
            print(f"ERROR saving receiving: {e}")
            return False
    
    def approve_receiving(self, job_number: str, manager_notes: str = "") -> bool:
        """Mark receiving as approved"""
        try:
            receiving = self.get_receiving_by_job(job_number)
            if not receiving:
                return False
            
            headers = self.client.get_headers(self.client.spreadsheet_id, "Receiving")
            
            # Set Approved to true
            receiving["Approved"] = "true"
            receiving["Complete"] = "true"
            if manager_notes:
                receiving["Manager Notes"] = manager_notes
            
            # Also update the valve status
            self.update_valve_status(job_number, "In Stripped")
            
            return self.save_receiving(receiving)
            
        except Exception as e:
            print(f"ERROR approving receiving: {e}")
            return False
    
    def reject_receiving(self, job_number: str, manager_notes: str = "") -> bool:
        """Mark receiving as rejected (needs rework)"""
        try:
            receiving = self.get_receiving_by_job(job_number)
            if not receiving:
                return False
            
            # Set Approved to false, keep Complete false
            receiving["Approved"] = "false"
            receiving["Complete"] = "false"
            if manager_notes:
                receiving["Manager Notes"] = manager_notes
            
            return self.save_receiving(receiving)
            
        except Exception as e:
            print(f"ERROR rejecting receiving: {e}")
            return False

