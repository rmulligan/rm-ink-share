import os
import json
import time
import textwrap
import re
from PIL import Image  # type: ignore

# --- Configuration ---
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"
QR_OUTPUT_PATH = "/home/ryan/pi_share_receiver/output/"

# Remarkable Pro tablet dimensions
RM_WIDTH = 1872  # Width in pixels for Remarkable Pro
RM_HEIGHT = 2404  # Height in pixels for Remarkable Pro
RM_MARGIN = 120  # Margin from edges
RM_LINE_HEIGHT = 35  # Space between lines of normal text
RM_HEADER_LINE_HEIGHT = 55  # Space for header lines
RM_MAX_TEXT_WIDTH = RM_WIDTH - (2 * RM_MARGIN)  # Maximum text width

# Font settings
RM_TITLE_FONT = "Lines-Bold"  # Font for titles
RM_HEADING_FONT = "Lines-Bold"  # Font for headings
RM_BODY_FONT = "Lines"  # Font for body text
RM_BODY_FONT_ITALIC = "Lines-Italic"  # Font for emphasizing text
RM_CODE_FONT = "Lines"  # Font for code blocks

# Font sizes
RM_TITLE_SIZE = 36
RM_H1_SIZE = 32
RM_H2_SIZE = 28
RM_H3_SIZE = 24
RM_BODY_SIZE = 18
RM_CODE_SIZE = 16

# Colors
RM_TEXT_COLOR = "#000000"  # Black for regular text
RM_ACCENT_COLOR = "#1C9BF0"  # Blue for headings and accents
RM_CODE_BG_COLOR = "#F2F2F2"  # Light gray for code backgrounds
RM_QUOTE_COLOR = "#6C757D"  # Gray for blockquotes
RM_LINK_COLOR = "#1C9BF0"  # Blue for links

def sanitize_text(text):
    """Sanitize text for use in HCL script."""
    if not text:
        return ""
    # Replace double quotes with escaped double quotes
    text = text.replace('"', '\\"')
    # Replace backslashes with double backslashes
    text = text.replace('\\', '\\\\')
    # Remove any non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text

def create_hcl_script(url, input_path, output_path):
    """
    Create an HCL script for drawj2d to generate a Remarkable document.
    
    Args:
        url: The URL being processed
        input_path: Path to the JSON file with content
        output_path: Path where to save the HCL file
    """
    try:
        print(f"Reading content from {input_path}")
        with open(input_path, 'r') as f:
            content = json.load(f)
        
        title = sanitize_text(content["title"])
        structured_content = content["structured_content"]
        
        print(f"Loaded content with title: {title}")
        print(f"Content has {len(structured_content)} elements")
        
        # Generate QR code for debugging
        qr_path = os.path.join(QR_OUTPUT_PATH, f"debug_qr_{int(time.time())}.png")
        
        # Create HCL script
        hcl_content = f"""# Remarkable document for URL: {url}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}
# Debug HCL file

puts "size {RM_WIDTH} {RM_HEIGHT}"

# Title
puts "set_font {RM_TITLE_FONT} {RM_TITLE_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN} \\"{title[:80]}\\""

# URL
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 2} \\"Source: {url}\\""
"""
        
        # Add content with more structure
        y_pos = RM_MARGIN + RM_LINE_HEIGHT * 5
        
        # Process all content types
        for idx, item in enumerate(structured_content):
            print(f"Processing content item {idx+1}: {item.get('type', 'unknown')} - {item.get('content', '')[:30]}...")
            
            item_type = item.get("type", "")
            
            if item_type == "paragraph":
                content_text = sanitize_text(item.get("content", ""))
                if content_text:
                    hcl_content += f'puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"\n'
                    
                    # Wrap long paragraphs
                    chunks = textwrap.wrap(content_text, width=80)
                    for chunk in chunks:
                        y_pos += RM_LINE_HEIGHT
                        hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{sanitize_text(chunk)}\\""\n'
            
            elif item_type.startswith("h") and len(item_type) == 2:
                # Handle headings
                heading_level = int(item_type[1])
                font_size = RM_H1_SIZE - (heading_level - 1) * 4
                if font_size < RM_BODY_SIZE:
                    font_size = RM_BODY_SIZE
                
                y_pos += RM_HEADER_LINE_HEIGHT
                heading_text = sanitize_text(item.get("content", ""))
                
                hcl_content += f'puts "set_font {RM_HEADING_FONT} {font_size}"\n'
                hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{heading_text}\\""\n'
                y_pos += RM_LINE_HEIGHT / 2
            
            elif item_type == "list":
                list_items = item.get("items", [])
                list_type = item.get("list_type", "ul")
                
                hcl_content += f'puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"\n'
                
                for i, list_item in enumerate(list_items):
                    y_pos += RM_LINE_HEIGHT
                    prefix = f"{i+1}. " if list_type == "ol" else "• "
                    item_text = sanitize_text(list_item)
                    
                    # Handle wrapping for list items
                    wrapped_text = textwrap.wrap(item_text, width=75)
                    
                    if wrapped_text:
                        # First line has bullet/number
                        hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{prefix}{wrapped_text[0]}\\""\n'
                        
                        # Subsequent lines are indented
                        for line in wrapped_text[1:]:
                            y_pos += RM_LINE_HEIGHT
                            hcl_content += f'puts "text {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
        
        # Add a debugging marker
        y_pos += RM_LINE_HEIGHT * 2
        hcl_content += f'puts "set_font {RM_BODY_FONT_ITALIC} {RM_BODY_SIZE}"\n'
        hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"DEBUG: Content processed with {len(structured_content)} items\\""\n'
        
        # Write HCL to file
        print(f"Writing HCL to {output_path}")
        with open(output_path, 'w') as f:
            f.write(hcl_content)
        
        print(f"HCL created successfully with {hcl_content.count('puts')} put statements")
        return output_path
    
    except Exception as e:
        print(f"Error creating HCL script: {e}")
        return None

# Execute the test
url = "https://docs.mulligan.dev/vGvJdpKgV7NFjB"
input_path = "/home/ryan/pi_share_receiver/temp/debug_simple.json"
output_path = "/home/ryan/pi_share_receiver/temp/debug_output.hcl"

create_hcl_script(url, input_path, output_path)
print("Done")