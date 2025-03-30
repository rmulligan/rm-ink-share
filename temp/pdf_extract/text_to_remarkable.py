#!/usr/bin/env python3
"""
Convert text content to an editable Remarkable document.

This script takes text content and creates a proper RM file
that can be edited on the Remarkable tablet.
"""

import os
import subprocess
import tempfile
import argparse
import time

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"

def generate_lines_hcl(text_content, title="Text Document"):
    """
    Generate HCL content using the Lines font with text command.
    This should create editable content.
    """
    lines_hcl = f"""# HCL for simple text document with Lines font
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Title: {title}

puts "size 1404 1872"  # Standard Remarkable size

# Set up pen and font
puts "pen black"
puts "line_width 1"
puts "set_font Lines 18"  # Using Lines font at readable size

# Add title (larger font)
puts "set_font Lines 24"
puts "text 100 100 \\"{title}\\""
puts "set_font Lines 18"  # Back to normal font size

"""
    
    # Split text into lines
    y_pos = 150  # Start position after title
    line_height = 30  # Height between lines
    
    # Process text by paragraphs
    paragraphs = text_content.split('\n\n')
    for para in paragraphs:
        lines = para.split('\n')
        for line in lines:
            if line.strip():
                # Clean and escape the line
                clean_line = line.strip().replace('\\', '\\\\').replace('"', '\\"')
                lines_hcl += f'puts "text 100 {y_pos} \\"{clean_line}\\""\n'
                y_pos += line_height
        
        # Add extra space between paragraphs
        y_pos += line_height
    
    # Create temporary file
    temp_hcl = os.path.join(TEMP_DIR, f"lines_text_{int(time.time())}.hcl")
    with open(temp_hcl, 'w') as f:
        f.write(lines_hcl)
    
    return temp_hcl

def create_rm_document(hcl_path, output_path=None):
    """Create RM document from HCL file."""
    if not output_path:
        output_path = os.path.join(TEMP_DIR, f"generated_doc_{int(time.time())}.rm")
    
    # Try with rm format
    cmd = [DRAWJ2D_PATH, "-T", "rm", "-o", output_path, hcl_path]
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error creating RM file: {result.stderr}")
        
        # Try with rmdoc format
        output_path = output_path.replace('.rm', '.rmdoc')
        cmd = [DRAWJ2D_PATH, "-T", "rmdoc", "-o", output_path, hcl_path]
        print(f"Trying rmdoc format: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error creating RMDOC file: {result.stderr}")
            return None
    
    return output_path

def upload_to_remarkable(file_path):
    """Upload file to Remarkable Cloud."""
    cmd = [RMAPI_PATH, "put", file_path, "/"]
    print(f"Uploading to Remarkable: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Convert text to editable Remarkable document')
    parser.add_argument('text_file', help='Text file to convert')
    parser.add_argument('--title', '-t', default=None, help='Document title')
    parser.add_argument('--output', '-o', default=None, help='Output file path')
    parser.add_argument('--upload', '-u', action='store_true', help='Upload to Remarkable')
    
    args = parser.parse_args()
    
    # Make sure text file exists
    if not os.path.exists(args.text_file):
        print(f"Error: Text file not found: {args.text_file}")
        return 1
    
    # Read text content
    with open(args.text_file, 'r') as f:
        text_content = f.read()
    
    # Use filename as title if not provided
    title = args.title
    if not title:
        title = os.path.basename(args.text_file)
    
    # Generate HCL file
    print(f"Generating HCL from text file: {args.text_file}")
    hcl_path = generate_lines_hcl(text_content, title)
    
    # Create RM document
    print("Creating Remarkable document...")
    rm_path = create_rm_document(hcl_path, args.output)
    
    if not rm_path:
        print("Failed to create Remarkable document")
        return 1
    
    print(f"Created Remarkable document: {rm_path}")
    
    # Upload if requested
    if args.upload:
        print("Uploading to Remarkable...")
        success = upload_to_remarkable(rm_path)
        if not success:
            print("Failed to upload to Remarkable")
            return 1
        print("Successfully uploaded to Remarkable")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())