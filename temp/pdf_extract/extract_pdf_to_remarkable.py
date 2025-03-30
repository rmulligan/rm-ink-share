#!/usr/bin/env python3
"""
PDF to Remarkable Conversion Tool

This script converts a PDF file to an editable Remarkable document using drawj2d.
It extracts the PDF content and creates an HCL script with vector paths that can
be properly edited on the Remarkable tablet.
"""

import os
import sys
import subprocess
import argparse
import time
import textwrap
from PyPDF2 import PdfReader  # type: ignore

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"
RM_WIDTH = 1872  # Width in pixels for Remarkable Pro
RM_HEIGHT = 2404  # Height in pixels for Remarkable Pro
RM_MARGIN = 120  # Margin from edges
RM_LINE_HEIGHT = 35  # Space between lines

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file."""
    try:
        print(f"Extracting text from PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        text_content = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content.append({
                    "page": i + 1,
                    "content": text
                })
        
        print(f"Extracted {len(text_content)} pages of text")
        return text_content
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []

def create_hcl_from_pdf_text(pdf_path, text_content, output_path=None):
    """Create an HCL script with vector paths from PDF text content."""
    try:
        print(f"Creating HCL script from PDF text")
        
        # Create filename if not provided
        if not output_path:
            basename = os.path.basename(pdf_path)
            name_without_ext = os.path.splitext(basename)[0]
            output_path = os.path.join(TEMP_DIR, f"{name_without_ext}.hcl")
        
        # Create HCL content
        hcl_content = f"""# Remarkable document converted from PDF: {pdf_path}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size {RM_WIDTH} {RM_HEIGHT}"

# Set up for vector paths (editable on device)
puts "line_width 1"
puts "line_color #000000"

# Title
puts "set_font Lines 36"
puts "text_to_path {RM_MARGIN} {RM_MARGIN} \\"PDF Conversion: {os.path.basename(pdf_path)}\\""

# Source info
puts "set_font Lines 18"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 60} \\"Source: {pdf_path}\\""
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 90} \\"Converted: {time.strftime("%Y-%m-%d %H:%M:%S")}\\""

"""
        
        y_pos = RM_MARGIN + 150
        
        # Process each page
        for page_data in text_content:
            page_num = page_data["page"]
            content = page_data["content"]
            
            # Add page header
            hcl_content += f'puts "set_font Lines 24"\n'
            hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"Page {page_num}\\""\n'
            y_pos += 50
            
            # Add page content
            hcl_content += f'puts "set_font Lines 18"\n'
            
            # Process line by line
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    # Wrap long lines
                    wrapped_lines = textwrap.wrap(line, width=70)
                    for wrapped in wrapped_lines:
                        # Escape text for HCL
                        escaped = wrapped.replace('\\', '\\\\').replace('"', '\\"')
                        hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"{escaped}\\""\n'
                        y_pos += RM_LINE_HEIGHT
                else:
                    # Add blank line
                    y_pos += RM_LINE_HEIGHT
            
            # Add page break
            y_pos += RM_LINE_HEIGHT * 2
            hcl_content += f'puts "line_width 1"\n'
            hcl_content += f'puts "pen lightgrey"\n'
            hcl_content += f'puts "moveto {RM_MARGIN} {y_pos}"\n'
            hcl_content += f'puts "lineto {RM_WIDTH - RM_MARGIN} {y_pos}"\n'
            hcl_content += f'puts "pen black"\n'
            y_pos += RM_LINE_HEIGHT * 2
        
        # Write HCL file
        with open(output_path, 'w') as f:
            f.write(hcl_content)
        
        print(f"Created HCL file at: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error creating HCL script: {e}")
        return None

def convert_to_remarkable(hcl_path, output_path=None, use_color=True):
    """Convert HCL to Remarkable format using drawj2d."""
    try:
        print(f"Converting HCL to Remarkable format")
        
        # Create output filename if not provided
        if not output_path:
            basename = os.path.basename(hcl_path)
            name_without_ext = os.path.splitext(basename)[0]
            output_path = os.path.join(TEMP_DIR, f"{name_without_ext}.rmdoc")
        
        # Convert to RMDOC format for Remarkable Pro
        cmd = [DRAWJ2D_PATH, "-Trmdoc"]
        
        # Add resolution parameter for Remarkable Pro
        if use_color:
            cmd.extend(["-r229"])
        
        cmd.extend(["-o", output_path, hcl_path])
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error converting to RMDOC: {result.stderr}")
            
            # Fallback to PDF
            print("Falling back to PDF format...")
            pdf_path = os.path.join(os.path.dirname(output_path), f"{os.path.splitext(os.path.basename(output_path))[0]}.pdf")
            cmd = [DRAWJ2D_PATH, "-Tpdf", "-o", pdf_path, hcl_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error converting to PDF: {result.stderr}")
                return None
            
            return pdf_path
        
        print(f"Successfully created Remarkable document: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error converting to Remarkable format: {e}")
        return None

def upload_to_remarkable(doc_path, folder="/"):
    """Upload document to Remarkable Cloud using rmapi."""
    try:
        print(f"Uploading to Remarkable Cloud: {doc_path}")
        
        cmd = [RMAPI_PATH, "put", doc_path, folder]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error uploading to Remarkable: {result.stderr}")
            return False
        
        print(f"Successfully uploaded to Remarkable: {os.path.basename(doc_path)}")
        return True
    except Exception as e:
        print(f"Error uploading to Remarkable: {e}")
        return False

def main():
    """Main function to process a PDF file and convert it to Remarkable format."""
    parser = argparse.ArgumentParser(description="Convert PDF to editable Remarkable document")
    parser.add_argument("pdf_path", help="Path to the PDF file to convert")
    parser.add_argument("--output", "-o", help="Output path for the Remarkable document")
    parser.add_argument("--upload", "-u", action="store_true", help="Upload to Remarkable after conversion")
    parser.add_argument("--folder", "-f", default="/", help="Remarkable folder to upload to")
    parser.add_argument("--color", "-c", action="store_true", help="Use color (for Remarkable Pro)")
    
    args = parser.parse_args()
    
    # Check if the PDF exists
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return 1
    
    # Extract text from PDF
    text_content = extract_text_from_pdf(args.pdf_path)
    if not text_content:
        print("Error: No text content extracted from PDF")
        return 1
    
    # Create HCL script
    hcl_path = create_hcl_from_pdf_text(args.pdf_path, text_content)
    if not hcl_path:
        print("Error: Failed to create HCL script")
        return 1
    
    # Convert to Remarkable format
    rm_path = convert_to_remarkable(hcl_path, args.output, args.color)
    if not rm_path:
        print("Error: Failed to convert to Remarkable format")
        return 1
    
    # Upload to Remarkable if requested
    if args.upload:
        success = upload_to_remarkable(rm_path, args.folder)
        if not success:
            print("Error: Failed to upload to Remarkable")
            return 1
    
    print("\nProcess completed successfully!")
    print(f"Remarkable document created: {rm_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())