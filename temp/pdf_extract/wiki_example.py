#!/usr/bin/env python3
"""
Implementation of the drawj2d wiki examples for Remarkable.

This script implements the exact approach described in the drawj2d
Sourceforge wiki for creating editable content on Remarkable tablets.
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

def create_write_hcl():
    """
    Create the write.hcl script exactly as described in the wiki.
    This script is used to convert text to Remarkable format.
    """
    write_hcl = """#!/usr/bin/env hecl
# write.hcl -- Write text onto a page
# Example usage:
#  drawj2d -Trmdoc write.hcl textfile.txt
#
# Requirements:
# * textfile.txt should have UTF-8 encoding

if {[llength $argv] < 1} {
    puts "usage: write.hcl <textfile>"
    exit
}

set filename [lindex $argv 0]

if {![file exists $filename]} {
    puts "Error: $filename does not exist."
    exit
}

# Open file and read contents
set f [open $filename r]
fconfigure $f -encoding utf-8
set text [read $f]
close $f

# Set font to single line font "Lines" with font size of 3.5 mm
# The Lines font supports Basic Latin, Latin-1, Greek, Latvian, Polish, Russian
# letters (Glyphs 0x20-0x7e 0xa0-0x17f 0x380-0x3f6 0x400-0x45f 0x490-0x4f9)
set fontname "Lines"
set fontsize 3.5

# Position of first line
set x 15
set y 5

# Maximum width of a line (x + maxw should not exceed the page width)
set maxw 138

# Write text to page
write_text $text $x $y $maxw $fontsize $fontname
"""
    
    write_hcl_path = os.path.join(TEMP_DIR, "write.hcl")
    with open(write_hcl_path, 'w') as f:
        f.write(write_hcl)
    
    return write_hcl_path

def convert_text_file(text_file_path, output_format="rmdoc"):
    """
    Convert a text file to Remarkable format using the write.hcl script.
    Uses the exact command from the wiki examples.
    """
    # Ensure write.hcl exists
    write_hcl_path = create_write_hcl()
    
    # Determine output path
    base_name = os.path.splitext(os.path.basename(text_file_path))[0]
    output_path = os.path.join(TEMP_DIR, f"{base_name}.{output_format}")
    
    # Run the command exactly as in the wiki
    cmd = [DRAWJ2D_PATH, f"-T{output_format}", "-o", output_path, write_hcl_path, text_file_path]
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    print(f"Successfully created {output_format.upper()} file: {output_path}")
    return output_path

def upload_to_remarkable(file_path):
    """Upload file to Remarkable Cloud."""
    cmd = [RMAPI_PATH, "put", file_path, "/"]
    print(f"Uploading to Remarkable: {file_path}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error uploading to Remarkable: {result.stderr}")
        return False
    
    print(f"Successfully uploaded {file_path} to Remarkable")
    return True

def create_text_from_url(url, output_file=None):
    """Create a text file from a URL for conversion."""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Create output file name if not provided
        if not output_file:
            timestamp = int(time.time())
            output_file = os.path.join(TEMP_DIR, f"url_content_{timestamp}.txt")
        
        # Fetch URL content
        print(f"Fetching content from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled"
        
        # Extract main content
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', class_='content') or 
            soup.find('div', id='content') or 
            soup.find('div', class_='main') or
            soup.find('div', class_='article') or
            soup.body
        )
        
        # Remove script, style, and nav elements
        if main_content:
            for element in main_content.select('script, style, nav, footer, header'):
                element.extract()
        
        # Extract text
        all_text = main_content.get_text('\n', strip=True) if main_content else soup.get_text('\n', strip=True)
        
        # Create formatted text content
        text_content = f"{title}\n\nSource: {url}\n\n{all_text}\n"
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"Created text file: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error creating text file from URL: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Convert content to Remarkable format using wiki example')
    parser.add_argument('--url', '-u', help='URL to convert')
    parser.add_argument('--text', '-t', help='Text file to convert')
    parser.add_argument('--format', '-f', choices=['rm', 'rmdoc', 'rmn'], default='rmdoc', 
                       help='Output format (default: rmdoc)')
    parser.add_argument('--upload', action='store_true', help='Upload to Remarkable after conversion')
    
    args = parser.parse_args()
    
    if not args.url and not args.text:
        print("Error: Must provide either --url or --text")
        return 1
    
    # Process URL if provided
    text_file = None
    if args.url:
        text_file = create_text_from_url(args.url)
        if not text_file:
            print("Failed to create text file from URL")
            return 1
    else:
        text_file = args.text
        if not os.path.exists(text_file):
            print(f"Error: Text file not found: {text_file}")
            return 1
    
    # Convert to Remarkable format
    rm_file = convert_text_file(text_file, args.format)
    if not rm_file:
        print("Failed to convert to Remarkable format")
        return 1
    
    # Upload if requested
    if args.upload:
        success = upload_to_remarkable(rm_file)
        if not success:
            print("Failed to upload to Remarkable")
            return 1
    
    print("Process completed successfully!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())