import os
import sys
import subprocess
import json
import time
import re
import textwrap

TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"
HCL_PATH = os.path.join(TEMP_DIR, f"pdf_test_{int(time.time())}.hcl")
PDF_PATH = os.path.join(TEMP_DIR, f"pdf_test_{int(time.time())}.pdf")

def create_hcl_from_content(content, output_path):
    """Create an HCL file from JSON content."""
    try:
        # Configurations
        width = 1404
        height = 1872
        margin = 120
        line_height = 35
        
        # Create HCL content
        hcl_content = f"""# PDF test file
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size {width} {height}"

# Title
puts "set_font Helvetica-Bold 36"
puts "text {margin} {margin} \\"{content.get('title', 'Untitled')[:80]}\\""

# Content
"""
        
        # Add content lines
        y_pos = margin + line_height * 3
        
        for item in content.get("structured_content", []):
            item_type = item.get("type", "")
            item_content = item.get("content", "")
            
            if not item_content:
                continue
                
            if item_type == "paragraph":
                hcl_content += f'puts "set_font Helvetica 18"\n'
                
                # Wrap long paragraphs
                chunks = textwrap.wrap(item_content, width=80)
                for chunk in chunks:
                    y_pos += line_height
                    safe_text = chunk.replace('"', '\\"').replace('\\', '\\\\')
                    hcl_content += f'puts "text {margin} {y_pos} \\"{safe_text}\\""\n'
            
            elif item_type.startswith("h") and len(item_type) == 2:
                # Handle headings
                heading_level = int(item_type[1])
                font_size = 32 - (heading_level - 1) * 4
                if font_size < 18:
                    font_size = 18
                
                y_pos += 50
                safe_text = item_content.replace('"', '\\"').replace('\\', '\\\\')
                
                hcl_content += f'puts "set_font Helvetica-Bold {font_size}"\n'
                hcl_content += f'puts "text {margin} {y_pos} \\"{safe_text}\\""\n'
                y_pos += line_height / 2
        
        # Add a debugging marker
        y_pos += line_height * 2
        hcl_content += f'puts "set_font Helvetica-Oblique 14"\n'
        hcl_content += f'puts "text {margin} {y_pos} \\"Debug: Content processed with {len(content.get("structured_content", []))} items\\""\n'
        
        # Write HCL to file
        with open(output_path, 'w') as f:
            f.write(hcl_content)
        
        print(f"HCL file created: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error creating HCL file: {e}")
        return None

def convert_hcl_to_pdf(hcl_path, pdf_path):
    """Convert HCL to PDF using drawj2d."""
    try:
        cmd = ["/usr/local/bin/drawj2d", "-v", "-F", "hcl", "-T", "pdf", "-o", pdf_path, hcl_path]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Conversion exit code: {result.returncode}")
        print(f"Conversion stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Conversion stderr: {result.stderr}")
        
        if os.path.exists(pdf_path):
            print(f"PDF created successfully: {pdf_path}")
            return pdf_path
        else:
            print(f"PDF file not created!")
            return None
        
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return None

def upload_pdf_to_remarkable(pdf_path, title):
    """Upload a PDF to Remarkable Cloud."""
    try:
        # Create a safe title
        safe_title = "".join([c if c.isalnum() or c in " .-_" else "_" for c in title])
        safe_title = safe_title[:50]
        
        cmd = ["/usr/local/bin/rmapi", "put", pdf_path, "/"]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Upload exit code: {result.returncode}")
        print(f"Upload stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Upload stderr: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Exception uploading PDF: {e}")
        return False

# Main execution
print("Testing PDF approach...")

# Load the JSON content
input_path = "/home/ryan/pi_share_receiver/temp/debug_simple.json"
with open(input_path, 'r') as f:
    content = json.load(f)

# Create HCL file
hcl_path = create_hcl_from_content(content, HCL_PATH)

# Convert to PDF
if hcl_path:
    pdf_path = convert_hcl_to_pdf(hcl_path, PDF_PATH)
    
    # Upload to Remarkable
    if pdf_path:
        if upload_pdf_to_remarkable(pdf_path, content.get("title", "Test")):
            print("Success! PDF uploaded to Remarkable.")
        else:
            print("Failed to upload PDF.")
    else:
        print("Failed to create PDF.")
else:
    print("Failed to create HCL file.")

print("Done")