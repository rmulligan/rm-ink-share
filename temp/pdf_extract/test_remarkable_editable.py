#!/usr/bin/env python3
"""
Test script to validate editable content creation for Remarkable.

This script creates an HCL file with vector paths using text_to_path commands
and converts it to RMDOC format using the correct parameters for Remarkable Pro.
"""

import os
import subprocess
import time

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RM_WIDTH = 1872  # Width in pixels for Remarkable Pro
RM_HEIGHT = 2404  # Height in pixels for Remarkable Pro
RM_MARGIN = 120  # Margin from edges

def create_test_hcl():
    """Create a test HCL file with text_to_path commands for editability."""
    print("Creating test HCL file...")
    
    hcl_content = f"""# Test Remarkable document with editable content
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size {RM_WIDTH} {RM_HEIGHT}"

# Set up for vector paths (editable on device)
puts "line_width 1"
puts "line_color #000000"

# Title using text_to_path
puts "set_font Lines 36"
puts "text_to_path {RM_MARGIN} {RM_MARGIN} \\"Editable Content Test\\""

# Subtitle
puts "set_font Lines 24"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 50} \\"This document tests vector text paths\\""

# Body text paragraphs
puts "set_font Lines 18"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 150} \\"This is a paragraph with text converted to vector paths.\\""
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 190} \\"All text should be editable on the Remarkable tablet.\\""
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 230} \\"The Lines font is a single-line font supported by drawj2d.\\""

# Italic text
puts "set_font Lines-Italic 18"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 310} \\"This text uses the Lines-Italic font.\\""

# Monospace text
puts "set_font LinesMono 18"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 390} \\"This text uses the LinesMono font for code.\\""

# Different sizes
puts "set_font Lines 24"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 470} \\"Larger text size (24pt)\\""
puts "set_font Lines 14"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 530} \\"Smaller text size (14pt)\\""

# Color test (for Remarkable Pro)
puts "pen inkblue"
puts "set_font Lines 24"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 610} \\"Blue text for Remarkable Pro\\""
puts "pen inkred"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 670} \\"Red text for Remarkable Pro\\""
puts "pen darkgreen"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + 730} \\"Green text for Remarkable Pro\\""

# Reset pen color
puts "pen black"
"""
    
    hcl_path = os.path.join(TEMP_DIR, "test_editable.hcl")
    with open(hcl_path, 'w') as f:
        f.write(hcl_content)
    
    print(f"Created HCL file at: {hcl_path}")
    return hcl_path

def convert_to_rmdoc(hcl_path):
    """Convert HCL to RMDOC format using proper resolution for Remarkable Pro."""
    print("Converting HCL to RMDOC format...")
    
    rmdoc_path = os.path.join(TEMP_DIR, "test_editable.rmdoc")
    
    # Use -r229 parameter as specified in the documentation for proper scaling on Remarkable Pro
    cmd = [DRAWJ2D_PATH, "-Trmdoc", "-r229", "-o", rmdoc_path, hcl_path]
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Result: {result.returncode}")
    if result.stdout:
        print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    if result.returncode != 0:
        print("RMDOC conversion failed, attempting PDF fallback...")
        pdf_path = os.path.join(TEMP_DIR, "test_editable.pdf")
        cmd = [DRAWJ2D_PATH, "-Tpdf", "-o", pdf_path, hcl_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully created PDF at: {pdf_path}")
            return pdf_path
        else:
            print("PDF conversion also failed.")
            return None
    
    print(f"Successfully created RMDOC at: {rmdoc_path}")
    return rmdoc_path

def main():
    """Create and convert a test document for Remarkable."""
    print("Testing Remarkable editable content creation...")
    
    # Create HCL file
    hcl_path = create_test_hcl()
    
    # Convert to RMDOC format
    output_path = convert_to_rmdoc(hcl_path)
    
    if output_path:
        print(f"\nTest completed successfully!")
        print(f"Test document created at: {output_path}")
        print("\nTo upload to Remarkable, use the rmapi command:")
        print(f"rmapi put \"{output_path}\" /")
    else:
        print("\nTest failed to create document.")

if __name__ == "__main__":
    main()