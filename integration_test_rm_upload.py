
#!/usr/bin/env python3
import os
import sys
import tempfile
import logging
from app.services.remarkable_service import RemarkableService

logging.basicConfig(level=logging.INFO)

def main():
    rmapi_path = os.getenv("RMAPI_PATH", "/usr/local/bin/rmapi")
    upload_folder = os.getenv("RM_UPLOAD_FOLDER", "/")
    
    # Use a dummy PDF header to simulate a valid PDF file for upload
    dummy_pdf_content = b"%PDF-1.4\n%Test Dummy PDF\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(dummy_pdf_content)
        temp_file_path = temp_file.name

    title = "Test Upload Notebook (Actual)"
    
    logging.info("Starting actual upload test to rmcloud")
    service = RemarkableService(rmapi_path, upload_folder)
    success, message = service.upload(temp_file_path, title)
    
    print("Integration Test Result:")
    print(f"Success: {success}")
    print(f"Message: {message}")
    print("Please check your rmcloud account for the new notebook if upload was successful.")
    
    # If ACTUAL_UPLOAD env variable is set (e.g., to "1"), retain the file for inspection; otherwise, delete it.
    if os.getenv("ACTUAL_UPLOAD", "0") != "1":
        os.remove(temp_file_path)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

