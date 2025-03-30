#!/usr/bin/env python3
"""
Final test script for Remarkable document creation.

This script creates two test files:
1. A minimal test file that should be viewable on the Remarkable
2. A PDF test file that should be guaranteed to display
"""

import os
import subprocess
import time

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"

def create_minimal_test():
    """Create a minimal test file that draws a single line of text."""
    
    print("Creating minimal test HCL...")
    hcl_content = """# Extreme minimal test
# Just one simple text line

puts "size 1404 1872"  # Standard remarkable size (portrait)
puts "line_width 1"
puts "pen black"
puts "moveto 100 200"
puts "lineto 500 200"
puts "set_font Lines 24"
puts "text_to_path 100 300 \\"Test Line - Created at {0}\\""
""".format(time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Write the HCL file
    hcl_path = os.path.join(TEMP_DIR, "final_minimal_test.hcl")
    with open(hcl_path, 'w') as f:
        f.write(hcl_content)
    
    print(f"Created HCL file at: {hcl_path}")
    
    # Convert to RMDOC
    print("Converting to RMDOC...")
    rmdoc_path = os.path.join(TEMP_DIR, "final_minimal_test.rmdoc")
    cmd = [DRAWJ2D_PATH, "-Trmdoc", "-o", rmdoc_path, hcl_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error converting to RMDOC: {result.stderr}")
        return None
    
    print(f"Created RMDOC at: {rmdoc_path}")
    return rmdoc_path

def create_pdf_test():
    """Create a PDF test file that should be guaranteed to display."""
    
    print("Creating PDF test HCL...")
    hcl_content = """# PDF test for Remarkable
# Generate a PDF that should display correctly

puts "size 1404 1872"  # Standard remarkable size (portrait)
puts "line_width 1"
puts "pen black"

# Draw a border
puts "moveto 100 100"
puts "lineto 1300 100"
puts "lineto 1300 1772"
puts "lineto 100 1772"
puts "lineto 100 100"

# Add title
puts "set_font Lines 36"
puts "text_to_path 200 200 \\"PDF Test Document\\""

# Add timestamp
puts "set_font Lines 18"
puts "text_to_path 200 250 \\"Created at {0}\\""

# Add testing text
puts "set_font Lines 24"
puts "text_to_path 200 400 \\"This is a test using PDF format\\""
puts "text_to_path 200 450 \\"This document should display on the Remarkable\\""

# Draw some shapes
puts "circle 300 600 50"
puts "rect 500 550 100 100"
puts "moveto 700 550"
puts "lineto 800 650"
puts "moveto 800 550"
puts "lineto 700 650"
""".format(time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Write the HCL file
    hcl_path = os.path.join(TEMP_DIR, "final_pdf_test.hcl")
    with open(hcl_path, 'w') as f:
        f.write(hcl_content)
    
    print(f"Created HCL file at: {hcl_path}")
    
    # Convert to PDF
    print("Converting to PDF...")
    pdf_path = os.path.join(TEMP_DIR, "final_pdf_test.pdf")
    cmd = [DRAWJ2D_PATH, "-Tpdf", "-o", pdf_path, hcl_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error converting to PDF: {result.stderr}")
        return None
    
    print(f"Created PDF at: {pdf_path}")
    return pdf_path

def upload_to_remarkable(file_path):
    """Upload a file to Remarkable Cloud."""
    if not file_path or not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        return False
    
    print(f"Uploading to Remarkable: {file_path}")
    cmd = [RMAPI_PATH, "put", file_path, "/"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error uploading to Remarkable: {result.stderr}")
        return False
    
    print("Successfully uploaded to Remarkable")
    return True

def main():
    """Run both test approaches."""
    print("=== Running final tests for Remarkable document creation ===")
    
    # Create and upload minimal test
    print("\n=== Minimal Test ===")
    minimal_path = create_minimal_test()
    if minimal_path:
        upload_to_remarkable(minimal_path)
    
    # Create and upload PDF test
    print("\n=== PDF Test ===")
    pdf_path = create_pdf_test()
    if pdf_path:
        upload_to_remarkable(pdf_path)
    
    print("\n=== Tests completed ===")
    print("Check your Remarkable tablet for the following files:")
    if minimal_path:
        print(f"- final_minimal_test.rmdoc")
    if pdf_path:
        print(f"- final_pdf_test.pdf")

if __name__ == "__main__":
    main()