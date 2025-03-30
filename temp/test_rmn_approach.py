import os
import sys
import subprocess
import json
import time
import re
import textwrap

TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"
RMAPI_PATH = "/usr/local/bin/rmapi"
HCL_PATH = os.path.join(TEMP_DIR, f"rmn_test_{int(time.time())}.hcl")
RMN_PATH = os.path.join(TEMP_DIR, f"rmn_test_{int(time.time())}.lines")

def create_hcl_from_content(content, output_path):
    """Create an HCL file from JSON content using vector drawing instructions."""
    try:
        # Configurations
        width = 1404
        height = 1872
        margin = 120
        line_height = 35
        
        # Create HCL content
        hcl_content = f"""# Remarkable Notebook Test
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size {width} {height}"

# Title as vector drawing (text can't be edited directly, but this preserves editability)
puts "line_width 3"
puts "line_color black"
"""
        
        # Title as vector/paths
        title = content.get('title', 'Untitled')
        y_pos = margin
        
        # Vector drawing initialization for text
        hcl_content += f'# Title: {title}\n'
        hcl_content += f'puts "set_font Helvetica-Bold 36"\n'
        hcl_content += f'puts "text_to_path {margin} {y_pos} \\"{title}\\"\n"\n'
        
        # URL as plain line drawing
        y_pos += line_height * 2
        url = "Source: " + content.get('url', 'Unknown URL')
        hcl_content += f'puts "set_font Helvetica 18"\n'
        hcl_content += f'puts "text_to_path {margin} {y_pos} \\"{url}\\"\n"\n'
        
        # Content - add a margin at the top
        y_pos += line_height * 3
        
        # Process all content
        for item in content.get("structured_content", []):
            item_type = item.get("type", "")
            item_content = item.get("content", "")
            
            if not item_content:
                continue
                
            if item_type == "paragraph":
                y_pos += line_height
                hcl_content += f'puts "set_font Helvetica 18"\n'
                
                # Wrap long paragraphs
                chunks = textwrap.wrap(item_content, width=70)
                for chunk in chunks:
                    safe_text = chunk.replace('"', '\\"').replace('\\', '\\\\')
                    hcl_content += f'puts "text_to_path {margin} {y_pos} \\"{safe_text}\\"\n"'
                    y_pos += line_height
                
                # Add extra spacing after paragraph
                y_pos += line_height/2
            
            elif item_type.startswith("h") and len(item_type) == 2:
                # Handle headings
                heading_level = int(item_type[1])
                font_size = 32 - (heading_level - 1) * 4
                if font_size < 18:
                    font_size = 18
                
                y_pos += line_height * 1.5
                safe_text = item_content.replace('"', '\\"').replace('\\', '\\\\')
                
                hcl_content += f'puts "set_font Helvetica-Bold {font_size}"\n'
                hcl_content += f'puts "text_to_path {margin} {y_pos} \\"{safe_text}\\"\n"'
                y_pos += line_height
        
        # Add a debugging marker
        y_pos += line_height * 2
        debug_text = f"Debug: Content processed with {len(content.get('structured_content', []))} items"
        hcl_content += f'puts "set_font Helvetica-Oblique 14"\n'
        hcl_content += f'puts "text_to_path {margin} {y_pos} \\"{debug_text}\\"\n"'
        
        # Write HCL to file
        with open(output_path, 'w') as f:
            f.write(hcl_content)
        
        print(f"HCL file created: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error creating HCL file: {e}")
        return None

def convert_hcl_to_rmn(hcl_path, rmn_path):
    """Convert HCL to RMN format using drawj2d."""
    try:
        cmd = [DRAWJ2D_PATH, "-v", "-F", "hcl", "-T", "rmn", "-o", rmn_path, hcl_path]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Conversion exit code: {result.returncode}")
        print(f"Conversion stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Conversion stderr: {result.stderr}")
        
        if os.path.exists(rmn_path):
            print(f"RMN file created successfully: {rmn_path}")
            return rmn_path
        else:
            print(f"RMN file not created!")
            return None
        
    except Exception as e:
        print(f"Error converting to RMN: {e}")
        return None

def upload_rmn_to_remarkable(rmn_path, title):
    """Upload RMN file to Remarkable Cloud."""
    try:
        # Create a safe title
        safe_title = "".join([c if c.isalnum() or c in " .-_" else "_" for c in title])
        safe_title = safe_title[:50]
        
        # Create a copy with proper extension
        safe_path = os.path.join(TEMP_DIR, f"{safe_title}.lines")
        import shutil
        shutil.copy2(rmn_path, safe_path)
        
        # Upload to Remarkable
        cmd = [RMAPI_PATH, "put", safe_path, "/"]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Upload exit code: {result.returncode}")
        print(f"Upload stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Upload stderr: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Exception uploading RMN: {e}")
        return False

# Main execution
print("Testing RMN approach...")

# Create test content
test_content = {
    "title": "Test RMN Format",
    "url": "https://docs.mulligan.dev/test",
    "structured_content": [
        {"type": "paragraph", "content": "This is a test paragraph to verify if RMN format works properly."},
        {"type": "paragraph", "content": "If this shows up on your ReMarkable tablet in editable form, the test was successful!"},
        {"type": "h1", "content": "Heading 1"},
        {"type": "paragraph", "content": "Content after heading 1"},
        {"type": "h2", "content": "Heading 2"},
        {"type": "paragraph", "content": "Content after heading 2"}
    ]
}

# Create HCL file
hcl_path = create_hcl_from_content(test_content, HCL_PATH)

# Convert to RMN
if hcl_path:
    rmn_path = convert_hcl_to_rmn(hcl_path, RMN_PATH)
    
    # Upload to Remarkable
    if rmn_path:
        if upload_rmn_to_remarkable(rmn_path, test_content.get("title", "Test")):
            print("Success! RMN uploaded to Remarkable.")
        else:
            print("Failed to upload RMN.")
    else:
        print("Failed to create RMN.")
else:
    print("Failed to create HCL file.")

print("Done")