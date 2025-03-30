import os
import sys
import subprocess
import json
import time
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"
OUTPUT_PATH = os.path.join(TEMP_DIR, f"test_png_{int(time.time())}.png")

# Create a PNG with the content instead
def create_image_with_content(content, output_path):
    """Create a PNG image with the content."""
    try:
        # Create an image
        width, height = 1404, 1872  # Remarkable dimensions
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Try to load a font
        try:
            # Try to use a system font
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
            font_body = ImageFont.truetype("DejaVuSans.ttf", 24)
        except:
            # Fallback to default
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        
        # Draw the title
        title = content.get("title", "Untitled")
        draw.text((100, 100), title, fill="black", font=font_title)
        
        # Draw the content
        y_pos = 200
        for item in content.get("structured_content", []):
            item_type = item.get("type", "")
            item_content = item.get("content", "")
            
            if item_content:
                # Wrap text to fit the image width
                wrapped_text = textwrap.fill(item_content, width=60)
                draw.text((100, y_pos), wrapped_text, fill="black", font=font_body)
                y_pos += 30 + wrapped_text.count('\n') * 30
        
        # Save the image
        image.save(output_path)
        print(f"Image saved to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error creating image: {e}")
        return None

# Upload a PNG to Remarkable Cloud
def upload_png_to_remarkable(png_path, title):
    """Upload a PNG to Remarkable Cloud."""
    try:
        cmd = ["/usr/local/bin/rmapi", "put", png_path, "/"]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Upload exit code: {result.returncode}")
        print(f"Upload stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Upload stderr: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Exception uploading PNG: {e}")
        return False

# Main execution
print("Testing new approach...")

# Load the JSON content
input_path = "/home/ryan/pi_share_receiver/temp/debug_simple.json"
with open(input_path, 'r') as f:
    content = json.load(f)

# Create a PNG
png_path = create_image_with_content(content, OUTPUT_PATH)

if png_path and upload_png_to_remarkable(png_path, content.get("title", "Test")):
    print("Success! PNG uploaded to Remarkable.")
else:
    print("Failed to create or upload PNG.")

print("Done")