#!/usr/bin/env python3
"""
Test converting web content to Remarkable format via markdown.

This approach:
1. Takes web content and formats it as markdown
2. Converts markdown to a simple HCL format using the md2rm approach
3. Uses drawj2d to convert directly to RM format
"""

import os
import subprocess
import time
import argparse
import tempfile
from bs4 import BeautifulSoup
import requests

# Settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"
RM_WIDTH = 1404  # Standard Remarkable width (portrait)
RM_HEIGHT = 1872  # Standard Remarkable height (portrait)

def scrape_url(url):
    """Scrape content from a URL and format as markdown."""
    try:
        print(f"Scraping URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else "Untitled"
        
        # Find main content
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', class_='content') or 
            soup.find('div', id='content') or 
            soup.find('div', class_='main') or
            soup.find('div', class_='article') or
            soup.body
        )
        
        # Remove script, style, and navigational elements
        if main_content:
            for element in main_content(["script", "style", "nav", "footer", "header", "aside"]):
                element.extract()
        
        # Build markdown content
        markdown = f"# {title}\n\n"
        markdown += f"Source: {url}\n\n"
        
        # Process headings
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                markdown += f"{'#' * i} {heading.get_text(strip=True)}\n\n"
        
        # Process paragraphs
        for p in soup.find_all('p'):
            markdown += f"{p.get_text(strip=True)}\n\n"
        
        # Add timestamp
        markdown += f"\n\n*Converted: {time.strftime('%Y-%m-%d %H:%M:%S')}*"
        
        print(f"Generated {len(markdown)} bytes of markdown content")
        return title, markdown
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return "Error", f"# Error Scraping URL\n\nFailed to scrape {url}: {str(e)}"

def create_direct_hcl(markdown_text):
    """Create HCL file using a different structure (similar to md2rm approach)."""
    hcl_content = f"""# Generated HCL for reMarkable
# Using direct approach similar to md2rm
# {time.strftime('%Y-%m-%d %H:%M:%S')}

puts "size {RM_WIDTH} {RM_HEIGHT}"

# Document structure
puts "line_width 1"
puts "pen black"

"""
    
    # Process markdown as simple text
    y_pos = 50  # Starting position
    line_height = 30  # Space between lines
    
    # Split text into paragraphs
    paragraphs = markdown_text.split('\n\n')
    for para in paragraphs:
        # Handle headings (lines starting with #)
        if para.startswith('# '):
            puts_line = f'puts "set_font Lines 36"'
            hcl_content += puts_line + "\n"
            text = para[2:]  # Remove the "# " prefix
            puts_line = f'puts "text {50} {y_pos} \\"{text}\\""'
            hcl_content += puts_line + "\n"
            y_pos += line_height * 2
        elif para.startswith('## '):
            puts_line = f'puts "set_font Lines 30"'
            hcl_content += puts_line + "\n"
            text = para[3:]  # Remove the "## " prefix
            puts_line = f'puts "text {50} {y_pos} \\"{text}\\""'
            hcl_content += puts_line + "\n"
            y_pos += line_height * 1.5
        elif para.startswith('### '):
            puts_line = f'puts "set_font Lines 24"'
            hcl_content += puts_line + "\n"
            text = para[4:]  # Remove the "### " prefix
            puts_line = f'puts "text {50} {y_pos} \\"{text}\\""'
            hcl_content += puts_line + "\n"
            y_pos += line_height * 1.2
        else:
            # Regular paragraph
            puts_line = f'puts "set_font Lines 18"'
            hcl_content += puts_line + "\n"
            
            # Handle line wrapping
            max_chars = 80  # Approximate max chars per line
            words = para.split()
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    # Output current line and start a new one
                    if current_line:
                        puts_line = f'puts "text {50} {y_pos} \\"{current_line}\\""'
                        hcl_content += puts_line + "\n"
                        y_pos += line_height
                        current_line = word
            
            # Output final line of paragraph
            if current_line:
                puts_line = f'puts "text {50} {y_pos} \\"{current_line}\\""'
                hcl_content += puts_line + "\n"
                y_pos += line_height
            
            # Add extra space after paragraph
            y_pos += line_height * 0.5
    
    # Create the HCL file
    hcl_path = os.path.join(TEMP_DIR, f"direct_rm_{int(time.time())}.hcl")
    with open(hcl_path, 'w') as f:
        f.write(hcl_content)
    
    print(f"Created HCL file: {hcl_path} ({len(hcl_content)} bytes)")
    return hcl_path

def generate_remarkable_document(hcl_path):
    """Generate reMarkable format directly using drawj2d with -Trm option."""
    try:
        print("Converting HCL to reMarkable format using direct method...")
        
        # Output path for the .rm file (use .rmdoc extension)
        rmdoc_path = os.path.join(TEMP_DIR, f"direct_rm_{int(time.time())}.rmdoc")
        
        # Use drawj2d with -Trm option
        cmd = [DRAWJ2D_PATH, "-Trm", "-o", rmdoc_path, hcl_path]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            # Try alternative formats
            print("Trying rmdoc format...")
            cmd = [DRAWJ2D_PATH, "-Trmdoc", "-o", rmdoc_path, hcl_path]
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"rmdoc format also failed: {result.stderr}")
                return None
        
        print(f"Successfully created reMarkable document: {rmdoc_path}")
        return rmdoc_path
    except Exception as e:
        print(f"Error generating reMarkable document: {e}")
        return None

def upload_to_remarkable(doc_path):
    """Upload document to Remarkable Cloud."""
    try:
        print(f"Uploading to Remarkable: {doc_path}")
        
        cmd = [RMAPI_PATH, "put", doc_path, "/"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error uploading to Remarkable: {result.stderr}")
            return False
        
        print(f"Successfully uploaded to Remarkable")
        return True
    except Exception as e:
        print(f"Error uploading to Remarkable: {e}")
        return False

def main():
    """Main function to process URL and convert to Remarkable format."""
    parser = argparse.ArgumentParser(description="Convert URL to editable Remarkable document")
    parser.add_argument("url", help="URL to process")
    parser.add_argument("--upload", "-u", action="store_true", help="Upload to Remarkable after conversion")
    
    args = parser.parse_args()
    
    # Scrape URL and convert to markdown
    title, markdown_content = scrape_url(args.url)
    
    # Create HCL file using direct approach
    hcl_path = create_direct_hcl(markdown_content)
    if not hcl_path:
        print("Failed to create HCL file")
        return 1
    
    # Generate Remarkable document
    rm_path = generate_remarkable_document(hcl_path)
    if not rm_path:
        print("Failed to generate Remarkable document")
        return 1
    
    # Upload to Remarkable if requested
    if args.upload:
        success = upload_to_remarkable(rm_path)
        if not success:
            print("Failed to upload to Remarkable")
            return 1
    
    print("\nProcess completed successfully!")
    print(f"Remarkable document created: {rm_path}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())