#!/usr/bin/env python3
"""Extended google_sheets.py - rename to google_sheets.py when ready"""

    # STRIPPED STAGE
    def get_stripped_by_job(self, job_number: str) -> Optional[Dict]:
        """Get stripped record for a valve"""
        try:
            headers = self.client.read_sheet(self.client.spreadsheet_id, "Stripped!A1:Z1")
            headers = headers[0] if headers else []
            data = self.client.read_sheet(self.client.spreadsheet_id, "Stripped!A2:Z1000")
            for i, row in enumerate(data):
                if not row or len(row) < 1:
                    continue
                job_col_idx = headers.index("Job Number") if "Job Number" in headers else 2
                if len(row) > job_col_idx and row[job_col_idx] == job_number:
                    stripped = {"_row_index": i + 2}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            stripped[header] = row[j]
                        else:
                            stripped[header] = ""
                    return stripped
            return None
        except Exception as e:
            print(f"ERROR getting stripped: {e}")
            return None

    def save_stripped(self, stripped_data: Dict) -> bool:
        """Save stripped record"""
        try:
            existing = self.get_stripped_by_job(stripped_data.get("Job Number"))
            headers = self.client.get_headers(self.client.spreadsheet_id, "Stripped")
            if not headers:
                print("ERROR: Could not get headers from Stripped sheet")
                return False
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")
                else:
                    row.append(stripped_data.get(header, ""))
            if existing:
                row_index = existing.get("_row_index")
                range_name = f"Stripped!A{row_index}:Z{row_index}"
                return self.client.update_row(self.client.spreadsheet_id, range_name, row)
            else:
                return self.client.append_row(self.client.spreadsheet_id, "Stripped!A1", row)
        except Exception as e:
            print(f"ERROR saving stripped: {e}")
            return False

    # BEFORE ASSEMBLY STAGE
    def get_before_assembly_by_job(self, job_number: str) -> Optional[Dict]:
        """Get before assembly record for a valve"""
        try:
            headers = self.client.read_sheet(self.client.spreadsheet_id, "BeforeAssembly!A1:Z1")
            headers = headers[0] if headers else []
            data = self.client.read_sheet(self.client.spreadsheet_id, "BeforeAssembly!A2:Z1000")
            for i, row in enumerate(data):
                if not row or len(row) < 1:
                    continue
                job_col_idx = headers.index("Job Number") if "Job Number" in headers else 2
                if len(row) > job_col_idx and row[job_col_idx] == job_number:
                    ba = {"_row_index": i + 2}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            ba[header] = row[j]
                        else:
                            ba[header] = ""
                    return ba
            return None
        except Exception as e:
            print(f"ERROR getting before assembly: {e}")
            return None

    def save_before_assembly(self, ba_data: Dict) -> bool:
        """Save before assembly record"""
        try:
            existing = self.get_before_assembly_by_job(ba_data.get("Job Number"))
            headers = self.client.get_headers(self.client.spreadsheet_id, "BeforeAssembly")
            if not headers:
                print("ERROR: Could not get headers from BeforeAssembly sheet")
                return False
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")
                else:
                    row.append(ba_data.get(header, ""))
            if existing:
                row_index = existing.get("_row_index")
                range_name = f"BeforeAssembly!A{row_index}:Z{row_index}"
                return self.client.update_row(self.client.spreadsheet_id, range_name, row)
            else:
                return self.client.append_row(self.client.spreadsheet_id, "BeforeAssembly!A1", row)
        except Exception as e:
            print(f"ERROR saving before assembly: {e}")
            return False

    # FINAL STAGE
    def get_final_by_job(self, job_number: str) -> Optional[Dict]:
        """Get final record for a valve"""
        try:
            headers = self.client.read_sheet(self.client.spreadsheet_id, "Final!A1:Z1")
            headers = headers[0] if headers else []
            data = self.client.read_sheet(self.client.spreadsheet_id, "Final!A2:Z1000")
            for i, row in enumerate(data):
                if not row or len(row) < 1:
                    continue
                job_col_idx = headers.index("Job Number") if "Job Number" in headers else 2
                if len(row) > job_col_idx and row[job_col_idx] == job_number:
                    final = {"_row_index": i + 2}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            final[header] = row[j]
                        else:
                            final[header] = ""
                    return final
            return None
        except Exception as e:
            print(f"ERROR getting final: {e}")
            return None

    def save_final(self, final_data: Dict) -> bool:
        """Save final record"""
        try:
            existing = self.get_final_by_job(final_data.get("Job Number"))
            headers = self.client.get_headers(self.client.spreadsheet_id, "Final")
            if not headers:
                print("ERROR: Could not get headers from Final sheet")
                return False
            row = []
            for header in headers:
                if header == "_RowNumber":
                    row.append("")
                else:
                    row.append(final_data.get(header, ""))
            if existing:
                row_index = existing.get("_row_index")
                range_name = f"Final!A{row_index}:Z{row_index}"
                return self.client.update_row(self.client.spreadsheet_id, range_name, row)
            else:
                return self.client.append_row(self.client.spreadsheet_id, "Final!A1", row)
        except Exception as e:
            print(f"ERROR saving final: {e}")
            return False
