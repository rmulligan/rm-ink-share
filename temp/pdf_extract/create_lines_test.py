#!/usr/bin/env python3
"""
Create a test file using Lines font to ensure proper display on Remarkable.

This script creates an HCL file with direct text commands using the Lines font,
then converts it to both PDF and RMDOC formats for comparison.
"""

import os
import subprocess
import tempfile
from uuid import uuid4
from zipfile import ZipFile
from datetime import datetime
import json

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"

def create_lines_hcl():
    """Create an HCL file with Lines font text."""
    
    hcl_content = """# Test with Lines font
# This should display properly on Remarkable with filled characters

puts "size 1404 1872"  # Standard Remarkable portrait

# Set up pen and font
puts "pen black"
puts "line_width 1"

# Title
puts "set_font Lines 36"
puts "text 100 100 \\"Lines Font Test\\""

# Subtitle with timestamp
puts "set_font Lines 24"
puts "text 100 150 \\"Created: TIMESTAMP\\""

# Body text
puts "set_font Lines 18"
puts "text 100 250 \\"This text uses the Lines font family.\\""
puts "text 100 300 \\"Characters should appear filled, not as outlines.\\""
puts "text 100 350 \\"The content should be editable on the Remarkable tablet.\\""

# Different sizes
puts "set_font Lines 28"
puts "text 100 450 \\"Larger text (28pt)\\""
puts "set_font Lines 14"
puts "text 100 500 \\"Smaller text (14pt)\\""

# Style variations
puts "set_font Lines-Italic 18"
puts "text 100 550 \\"Italic text using Lines-Italic\\""
puts "set_font LinesMono 18"
puts "text 100 600 \\"Monospace text using LinesMono\\""

# Line drawing
puts "line_width 2"
puts "moveto 100 650"
puts "lineto 600 650"

# Bullet points
puts "set_font Lines 18"
puts "text 100 700 \\"• First bullet point\\""
puts "text 100 750 \\"• Second bullet point\\""
puts "text 100 800 \\"• Third bullet point with longer text that might wrap to another line\\""
"""
    
    # Replace timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hcl_content = hcl_content.replace("TIMESTAMP", timestamp)
    
    # Create HCL file
    hcl_path = os.path.join(TEMP_DIR, "lines_test.hcl")
    with open(hcl_path, 'w') as f:
        f.write(hcl_content)
    
    print(f"Created HCL file with Lines font: {hcl_path}")
    return hcl_path

def convert_to_pdf(hcl_path):
    """Convert HCL to PDF format."""
    pdf_path = os.path.join(TEMP_DIR, "lines_test.pdf")
    
    cmd = [DRAWJ2D_PATH, "-Tpdf", "-o", pdf_path, hcl_path]
    print(f"Converting to PDF: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error converting to PDF: {result.stderr}")
        return None
    
    print(f"Created PDF: {pdf_path}")
    return pdf_path

def convert_to_rm(hcl_path):
    """Convert HCL to RM format."""
    rm_path = os.path.join(TEMP_DIR, "lines_test.rm")
    
    cmd = [DRAWJ2D_PATH, "-Trm", "-o", rm_path, hcl_path]
    print(f"Converting to RM: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error converting to RM: {result.stderr}")
        return None
    
    print(f"Created RM file: {rm_path}")
    return rm_path

def create_rmdoc_from_rm(rm_path):
    """Create an RMDOC file from a single RM file."""
    rmdoc_path = os.path.join(TEMP_DIR, "lines_test.rmdoc")
    
    # Generate UUIDs
    document_uuid = str(uuid4())
    page_uuid = str(uuid4())
    
    # Get current timestamp
    timestamp = int(datetime.now().timestamp() * 1000)
    
    # Create the RMDOC file (ZIP archive)
    with ZipFile(rmdoc_path, 'w') as output_zip:
        # Create page definitions
        page_list = [{
            "id": page_uuid,
            "idx": {
                "timestamp": "1:2",
                "value": "ba"  # First page index
            }
        }]
        
        # Write metadata file
        output_zip.writestr(f"{document_uuid}.metadata", json.dumps({
            "createdTime": f"{timestamp}",
            "lastModified": f"{timestamp}",
            "lastOpened": f"{timestamp}",
            "lastOpenedPage": 0,
            "parent": "",
            "pinned": False,
            "type": "DocumentType",
            "visibleName": "Lines Font Test"
        }, indent=4))
        
        # Write content file
        output_zip.writestr(f"{document_uuid}.content", json.dumps({
            "cPages": {
                "original": {
                    "timestamp": "0:0",
                    "value": -1
                },
                "pages": page_list
            },
            "coverPageNumber": -1,
            "customZoomCenterX": 0,
            "customZoomCenterY": 936,
            "customZoomOrientation": "portrait",
            "customZoomPageHeight": 1872,
            "customZoomPageWidth": 1404,
            "customZoomScale": 1,
            "documentMetadata": {},
            "extraMetadata": {
                "LastActiveTool": "primary",
                "LastBallpointv2Color": "Red",
                "LastBallpointv2Size": "2",
                "LastEraserColor": "Black",
                "LastEraserSize": "2",
                "LastEraserTool": "Eraser",
                "LastHighlighterv2Color": "ArgbCode",
                "LastHighlighterv2ColorCode": "4294951820",
                "LastHighlighterv2Size": "1",
                "LastPen": "Ballpointv2",
                "LastPencilv2Color": "Red",
                "LastPencilv2Size": "3",
                "LastSelectionToolColor": "Black",
                "LastSelectionToolSize": "2",
                "SecondaryHighlighterv2Color": "ArgbCode",
                "SecondaryHighlighterv2ColorCode": "4294962549",
                "SecondaryHighlighterv2Size": "1",
                "SecondaryPen": "Highlighterv2"
            },
            "fileType": "notebook",
            "fontName": "",
            "formatVersion": 2,
            "lineHeight": -1,
            "margins": 125,
            "orientation": "portrait",
            "pageCount": 1,
            "pageTags": [],
            "sizeInBytes": "0",
            "tags": [],
            "textAlignment": "justify",
            "textScale": 1,
            "zoomMode": "bestFit"
        }, indent=4))
        
        # Add the RM file
        output_zip.write(rm_path, f'{document_uuid}/{page_uuid}.rm')
    
    print(f"Created RMDOC file: {rmdoc_path}")
    return rmdoc_path

def upload_to_remarkable(file_path):
    """Upload to Remarkable Cloud."""
    cmd = [RMAPI_PATH, "put", file_path, "/"]
    print(f"Uploading to Remarkable: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error uploading to Remarkable: {result.stderr}")
        return False
    
    print(f"Successfully uploaded to Remarkable: {file_path}")
    return True

def main():
    """Run all conversion tests."""
    # Create HCL file with Lines font
    hcl_path = create_lines_hcl()
    
    # Convert to PDF for reference
    pdf_path = convert_to_pdf(hcl_path)
    
    # Create RM file directly
    rm_path = convert_to_rm(hcl_path)
    
    # Create RMDOC from RM file
    if rm_path:
        rmdoc_path = create_rmdoc_from_rm(rm_path)
        
        # Upload RMDOC to Remarkable
        if rmdoc_path:
            upload_to_remarkable(rmdoc_path)
    
    # Upload PDF as reference
    if pdf_path:
        upload_to_remarkable(pdf_path)
    
    print("Test complete.")

if __name__ == "__main__":
    main()