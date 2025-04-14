
#!/usr/bin/env python3
import os
import sys
import tempfile
import logging
from app.services.remarkable_service import RemarkableService
from app.services.document_service import DocumentService

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
    
    # Conversion Test: Validate the output file format from conversion process
    temp_dir = tempfile.gettempdir()
    ds = DocumentService(temp_dir, "/usr/local/bin/drawj2d")
    dummy_hcl_path = os.path.join(temp_dir, "dummy.hcl")
    rm_output_path = os.path.join(temp_dir, "dummy_output.rmdoc")
    with open(dummy_hcl_path, "w", encoding="utf-8") as f:
         f.write('puts "size 1872 2404"\n')
         f.write('puts "font \\"Lines\\""\n')
         f.write('puts "pen black"\n')
         f.write('puts "text 100 100 \\"Dummy Title\\""\n')
    conv_result = ds._convert_to_remarkable(dummy_hcl_path, rm_output_path)
    if conv_result is None or not os.path.exists(rm_output_path):
         print("Conversion Test Failed: Output file not created.")
         sys.exit(1)
    else:
         with open(rm_output_path, "rb") as f:
              conv_preview = f.read(100)
         print("Conversion Test Result:")
         print(f"Output file: {rm_output_path}, size: {os.path.getsize(rm_output_path)} bytes")
         print(f"Preview (100 bytes): {conv_preview}")
         os.remove(dummy_hcl_path)
         os.remove(rm_output_path)
    
    if os.getenv("ACTUAL_UPLOAD", "0") != "1":
        os.remove(temp_file_path)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

