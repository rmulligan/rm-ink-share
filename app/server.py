from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import qrcode  # type: ignore
import os
import subprocess
import requests
import tempfile
import io
import time
import textwrap
import re
import base64
import uuid
from PIL import Image  # type: ignore # Requires pillow, installed via "qrcode[pil]"
from bs4 import BeautifulSoup  # type: ignore
import PyPDF2  # For PDF extraction

# --- Configuration ---
LISTEN_HOST = '0.0.0.0'  # Listen on all available interfaces, including Tailscale
LISTEN_PORT = 9999       # Using a different port since others are already in use
QR_OUTPUT_PATH = "/home/ryan/pi_share_receiver/output/"  # Using absolute path for reliability
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"  # Temporary directory for processing
RMAPI_PATH = "/usr/local/bin/rmapi"  # Path to rmapi executable
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"  # Path to drawj2d executable
RM_FOLDER = "/"  # Remarkable cloud folder to upload to (root by default)

# PDF extraction tools
PDF_EXTRACT_PATH = "/home/ryan/pi_share_receiver/temp/pdf_extract/"

# Remarkable Pro tablet dimensions
RM_WIDTH = 1872  # Width in pixels for Remarkable Pro (increased from standard)
RM_HEIGHT = 2404  # Height in pixels for Remarkable Pro (increased from standard)
RM_MARGIN = 120  # Margin from edges
RM_LINE_HEIGHT = 35  # Space between lines of normal text
RM_HEADER_LINE_HEIGHT = 55  # Space for header lines
RM_MAX_TEXT_WIDTH = RM_WIDTH - (2 * RM_MARGIN)  # Maximum text width

# Font settings for Remarkable Pro
# Body text uses Lines font for editability
# Headings can use non-Lines fonts since they'll be filled in manually or as PNG
RM_TITLE_FONT = "Roman"  # Font for titles - can be any drawj2d font since you'll fill it in
RM_HEADING_FONT = "Roman"  # Font for headings - visible as outlines for Remarkable Pro
RM_BODY_FONT = "Lines"  # Font for body text - must use Lines for proper filled characters
RM_BODY_FONT_ITALIC = "Lines-Italic"  # For emphasizing text - use Lines-Italic for editability
RM_CODE_FONT = "LinesMono"  # For code blocks - use LinesMono for monospaced content

# Font sizes
RM_TITLE_SIZE = 36
RM_H1_SIZE = 32
RM_H2_SIZE = 28
RM_H3_SIZE = 24
RM_BODY_SIZE = 18
RM_CODE_SIZE = 16

# Colors (for Remarkable Pro)
RM_TEXT_COLOR = "#000000"  # Black for regular text
RM_ACCENT_COLOR = "#1C9BF0"  # Blue for headings and accents
RM_CODE_BG_COLOR = "#F2F2F2"  # Light gray for code backgrounds
RM_QUOTE_COLOR = "#6C757D"  # Gray for blockquotes
RM_LINK_COLOR = "#1C9BF0"  # Blue for links
# --- End Configuration ---

# Ensure directories exist
os.makedirs(QR_OUTPUT_PATH, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PDF_EXTRACT_PATH, exist_ok=True)

def is_pdf_url(url):
    """
    Check if a URL points to a PDF file.
    
    Args:
        url: The URL to check
        
    Returns:
        True if the URL appears to point to a PDF, False otherwise
    """
    # Check if the URL ends with .pdf
    if url.lower().endswith('.pdf'):
        return True
    
    try:
        # Get headers only - don't download the whole file
        headers = requests.head(url, allow_redirects=True, timeout=10).headers
        content_type = headers.get('Content-Type', '').lower()
        
        return 'application/pdf' in content_type
    except Exception as e:
        print(f"Error checking if URL is PDF: {e}")
        return False
        
def process_pdf_url(url, qr_image_path):
    """
    Process a PDF URL to create an editable Remarkable document.
    
    Args:
        url: The URL of the PDF to process
        qr_image_path: Path to QR code image for the URL
        
    Returns:
        Path to the created Remarkable document or None on failure
    """
    try:
        print(f"Processing PDF URL: {url}")
        
        # Download the PDF
        pdf_filename = f"temp_pdf_{int(time.time())}.pdf"
        pdf_path = os.path.join(TEMP_DIR, pdf_filename)
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded PDF from {url} to {pdf_path}")
        
        # Get PDF title
        title = "PDF Document"
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                else:
                    # Extract title from URL if no metadata title
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.split('/')
                    if path_parts and path_parts[-1]:
                        # Get filename without extension
                        title = os.path.splitext(path_parts[-1])[0].replace('_', ' ').replace('-', ' ')
        except Exception as e:
            print(f"Error extracting PDF title: {e}")
        
        # Extract text from PDF
        extract_script = os.path.join(PDF_EXTRACT_PATH, "extract_pdf_text.py")
        
        # Check if the script exists
        if not os.path.exists(extract_script):
            print(f"Error: PDF extraction script not found at {extract_script}")
            # Create a simple HCL script directly as fallback
            hcl_filename = f"pdf_{hash(url)}_{int(time.time())}.hcl"
            hcl_path = os.path.join(TEMP_DIR, hcl_filename)
            
            # Create a basic HCL with title and URL
            with open(hcl_path, 'w') as f:
                f.write(f"""# Remarkable document for PDF: {url}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size 1404 1872"  # Standard Remarkable size (portrait)

puts "pen black"
puts "line_width 1"

# Title
puts "set_font {RM_TITLE_FONT} {RM_TITLE_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN} \\"{title}\\""

# URL
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 2} \\"Source: {url}\\""

# PDF Extraction fallback message
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 4} \\"PDF content could not be extracted automatically.\\""
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 5} \\"Please view the PDF directly on your device.\\""
""")
            print(f"Created fallback HCL script at {hcl_path}")
            return hcl_path
        
        # Create an HCL script from the extracted text
        hcl_filename = f"pdf_{hash(url)}_{int(time.time())}.hcl"
        hcl_path = os.path.join(TEMP_DIR, hcl_filename)
        
        # Run the extraction script with more detailed output
        print(f"Running PDF extraction: python {extract_script} {pdf_path} --hcl --title \"{title}\"")
        extract_cmd = ["python", extract_script, pdf_path, "--hcl", "--title", title]
        extract_result = subprocess.run(extract_cmd, capture_output=True, text=True)
        
        print(f"PDF extraction return code: {extract_result.returncode}")
        if extract_result.stdout:
            print(f"PDF extraction stdout: {extract_result.stdout[:200]}...")
        if extract_result.stderr:
            print(f"PDF extraction stderr: {extract_result.stderr[:200]}...")
        
        if extract_result.returncode != 0:
            print(f"Error extracting PDF content: {extract_result.stderr}")
            # Create a simple HCL script directly as fallback
            with open(hcl_path, 'w') as f:
                f.write(f"""# Remarkable document for PDF: {url}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size 1404 1872"  # Standard Remarkable size (portrait)

puts "pen black"
puts "line_width 1"

# Title
puts "set_font {RM_TITLE_FONT} {RM_TITLE_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN} \\"{title}\\""

# URL
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 2} \\"Source: {url}\\""

# PDF Extraction error message
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 4} \\"PDF extraction error: {extract_result.returncode}\\""
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 5} \\"Please view the PDF directly on your device.\\""
""")
            print(f"Created fallback HCL script due to extraction error: {hcl_path}")
            return hcl_path
        
        # Add QR code to the HCL script
        if os.path.exists(qr_image_path):
            # Find the HCL file that was created
            for file in os.listdir(TEMP_DIR):
                if file.endswith('.hcl') and file.startswith(f"pdf_{hash(url)}"):
                    hcl_path = os.path.join(TEMP_DIR, file)
                    break
            
            if os.path.exists(hcl_path):
                # Add QR code to the top-right corner
                with open(hcl_path, 'r') as f:
                    hcl_content = f.read()
                
                # Add QR code command after "size" definition
                qr_size = 350
                qr_x = RM_WIDTH - RM_MARGIN - qr_size
                qr_y = RM_MARGIN
                qr_cmd = f'puts "image {qr_x} {qr_y} {qr_size} {qr_size} \\"{qr_image_path}\\""'
                
                # Insert QR code command after the size definition
                if 'puts "size' in hcl_content:
                    lines = hcl_content.split('\n')
                    for i, line in enumerate(lines):
                        if 'puts "size' in line:
                            lines.insert(i+1, "# QR Code")
                            lines.insert(i+2, qr_cmd)
                            break
                    
                    # Write back the modified content
                    with open(hcl_path, 'w') as f:
                        f.write('\n'.join(lines))
                    
                    print(f"Added QR code to HCL script: {hcl_path}")
        
        # Convert to Remarkable format
        print(f"Converting PDF content to Remarkable format")
        convert_script = os.path.join(PDF_EXTRACT_PATH, "pdf_to_remarkable.py")
        
        # Create the file directly from the HCL script
        rm_filename = f"rm_{hash(url)}_{int(time.time())}.rm"
        rm_path = os.path.join(TEMP_DIR, rm_filename)
        
        # Convert HCL to RM format using drawj2d with Remarkable Pro resolution
        # Note: Current drawj2d creates v5 files but they're compatible with Remarkable Pro
        # The key is using Lines font family which ensures proper filled characters
        cmd = [DRAWJ2D_PATH, "-Trm", "-r229", "-o", rm_path, hcl_path]
        print(f"Converting HCL to RM format for Remarkable Pro: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error converting to RM format: {result.stderr}")
            # Try creating a RMDOC package from the HCL
            return create_rmdoc_from_hcl(hcl_path, url)
        
        # Verify the file exists
        if not os.path.exists(rm_path):
            print(f"Error: RM file was not created at {rm_path}")
            return None
        
        print(f"Successfully created RM file for PDF: {rm_path}")
        return rm_path
        
    except Exception as e:
        print(f"Error processing PDF URL: {e}")
        return None

def scrape_webpage(url):
    """Scrape content from a URL and return the title, structured content, and images."""
    try:
        # For all URLs, first check if it's a PDF
        if is_pdf_url(url):
            print(f"Detected PDF URL: {url}")
            return {
                "title": f"PDF Document: {url}",
                "structured_content": [{
                    "type": "paragraph",
                    "content": f"This is a PDF document. It will be processed with the PDF extractor."
                }],
                "images": []
            }
        
        # Always use the JavaScript-enabled scraper for modern websites
        print(f"Using JS-enabled scraper for URL: {url}")
        return scrape_with_js(url)
        
    except Exception as e:
        print(f"Error scraping webpage: {e}")
        return {
            "title": f"Error: Could not scrape {url}", 
            "structured_content": [{
                "type": "paragraph", 
                "content": f"Failed to scrape content: {str(e)}"
            }],
            "images": []
        }

def scrape_with_js(url):
    """Scrape a webpage using Playwright for JavaScript-enabled content."""
    try:
        # Create a unique filename for the output
        output_filename = f"js_output_{int(time.time())}.json"
        output_path = os.path.join(TEMP_DIR, output_filename)
        
        # Path to the Python script
        script_path = "/home/ryan/pi_share_receiver/app/scrape_js.py"
        
        # Run the Playwright scraper script
        cmd = ["python", script_path, url, output_path]
        print(f"Running JS-enabled scraper: {' '.join(cmd)}")
        
        # Set a longer timeout for JavaScript rendering (2 minutes)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"JS scraper output: {result.stdout}")
        if result.stderr:
            print(f"JS scraper errors: {result.stderr}")
        
        if result.returncode != 0:
            print(f"Error running JS scraper: {result.stderr}")
            return {
                "title": f"Error: Could not scrape {url}", 
                "structured_content": [{
                    "type": "paragraph", 
                    "content": f"Failed to scrape content: {result.stderr}"
                }],
                "images": []
            }
        
        # Check if the output file exists
        if not os.path.exists(output_path):
            print(f"Output file not found: {output_path}")
            return {
                "title": f"Error: Could not scrape {url}", 
                "structured_content": [{
                    "type": "paragraph", 
                    "content": f"Script did not produce output file"
                }],
                "images": []
            }
        
        # Read the output file
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        return {
            "title": content.get("title", "Untitled"), 
            "structured_content": content.get("structured_content", []),
            "images": content.get("images", [])
        }
    except Exception as e:
        print(f"Error in JavaScript-enabled scraping: {e}")
        return {
            "title": f"Error: Could not scrape {url}", 
            "structured_content": [{
                "type": "paragraph", 
                "content": f"Failed to scrape content: {str(e)}"
            }],
            "images": []
        }

def process_content_elements(element, content_list, image_list, base_url):
    """Process HTML elements and extract structured content."""
    # Process headings
    for i in range(1, 7):
        for heading in element.find_all(f'h{i}', recursive=False):
            content_list.append({
                "type": f"h{i}",
                "content": heading.get_text(strip=True)
            })
            heading.extract()
    
    # Process images
    for img in element.find_all('img', recursive=False):
        src = img.get('src', '')
        alt = img.get('alt', 'Image')
        
        # Handle relative URLs
        if src and not src.startswith(('http://', 'https://')):
            src = requests.compat.urljoin(base_url, src)
        
        if src:
            img_id = str(uuid.uuid4())
            image_list.append({
                "id": img_id,
                "src": src,
                "alt": alt
            })
            content_list.append({
                "type": "image",
                "image_id": img_id,
                "alt": alt
            })
        img.extract()
    
    # Process pre/code blocks
    for pre in element.find_all(['pre', 'code'], recursive=False):
        content_list.append({
            "type": "code",
            "content": pre.get_text(strip=True)
        })
        pre.extract()
    
    # Process paragraphs
    for p in element.find_all('p', recursive=False):
        # Check if paragraph has images
        has_processed_content = False
        
        # Process nested images
        for img in p.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', 'Image')
            
            # Handle relative URLs
            if src and not src.startswith(('http://', 'https://')):
                src = requests.compat.urljoin(base_url, src)
            
            if src:
                img_id = str(uuid.uuid4())
                image_list.append({
                    "id": img_id,
                    "src": src,
                    "alt": alt
                })
                content_list.append({
                    "type": "image",
                    "image_id": img_id,
                    "alt": alt
                })
                has_processed_content = True
        
        # Add the text content if not empty
        text = p.get_text(strip=True)
        if text:
            content_list.append({
                "type": "paragraph",
                "content": text
            })
            has_processed_content = True
        
        p.extract()
    
    # Process lists
    for list_el in element.find_all(['ul', 'ol'], recursive=False):
        list_items = []
        for li in list_el.find_all('li'):
            list_items.append(li.get_text(strip=True))
        
        content_list.append({
            "type": "list",
            "list_type": list_el.name,  # 'ul' or 'ol'
            "items": list_items
        })
        list_el.extract()
    
    # Process blockquotes
    for blockquote in element.find_all('blockquote', recursive=False):
        content_list.append({
            "type": "blockquote",
            "content": blockquote.get_text(strip=True)
        })
        blockquote.extract()
    
    # Process remaining text
    text = element.get_text(strip=True)
    if text:
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                content_list.append({
                    "type": "paragraph",
                    "content": paragraph.strip()
                })
    
    # Process children recursively
    for child in element.children:
        if hasattr(child, 'name') and child.name:
            process_content_elements(child, content_list, image_list, base_url)

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

def download_image(image_url, image_id):
    """Download an image and save it to the temp directory."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Determine file extension based on content type
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'svg' in content_type:
            ext = 'svg'
        else:
            ext = 'jpg'  # Default to jpg
        
        image_path = os.path.join(TEMP_DIR, f"{image_id}.{ext}")
        
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        return image_path, ext
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")
        return None, None

def create_hcl_script(url, qr_image_path, content):
    """Create an HCL script with Lines font for editable content on Remarkable."""
    try:
        title = sanitize_text(content["title"])
        structured_content = content["structured_content"]
        images = content["images"]
        
        # Download images
        image_paths = {}
        for img in images:
            img_path, img_ext = download_image(img["src"], img["id"])
            if img_path:
                image_paths[img["id"]] = img_path
        
        # Create HCL script using the Lines font with text command
        # This ensures characters appear filled, not as outlines
        hcl_content = f"""# Remarkable document for URL: {url}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size 1404 1872"  # Standard Remarkable size (portrait)

# Set up for editable text with proper font
puts "pen black"
puts "line_width 1"

# Title
puts "set_font Lines {RM_TITLE_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN} \\"{title[:80]}\\""

# URL
puts "set_font Lines {RM_BODY_SIZE}"
puts "text {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 2} \\"Source: {url}\\""

# QR Code
"""
        
        # Add QR code
        if os.path.exists(qr_image_path):
            qr_size = 350
            qr_x = RM_WIDTH - RM_MARGIN - qr_size
            qr_y = RM_MARGIN
            hcl_content += f'puts "image {qr_x} {qr_y} {qr_size} {qr_size} \\"{qr_image_path}\\""\n'
        
        # Add content with more structure
        y_pos = RM_MARGIN + RM_LINE_HEIGHT * 5
        
        # Process all content types
        for idx, item in enumerate(structured_content):
            item_type = item.get("type", "")
            
            # Handle different content types
            if item_type == "paragraph":
                content_text = sanitize_text(item.get("content", ""))
                if content_text:
                    hcl_content += f'puts "set_font Lines {RM_BODY_SIZE}"\n'
                    
                    # Wrap long paragraphs to prevent horizontal overflow
                    chunks = textwrap.wrap(content_text, width=70)
                    for chunk in chunks:
                        y_pos += RM_LINE_HEIGHT
                        hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{sanitize_text(chunk)}\\""\n'
                    
                    # Add extra spacing after paragraph
                    y_pos += RM_LINE_HEIGHT / 2
            
            elif item_type.startswith("h") and len(item_type) == 2:
                # Handle headings (h1, h2, h3, etc.)
                heading_level = int(item_type[1])
                font_size = RM_H1_SIZE - (heading_level - 1) * 4  # Decrease size for each level
                if font_size < RM_BODY_SIZE:
                    font_size = RM_BODY_SIZE
                
                y_pos += RM_HEADER_LINE_HEIGHT
                heading_text = sanitize_text(item.get("content", ""))
                
                hcl_content += f'puts "set_font Lines {font_size}"\n'
                hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{heading_text}\\""\n'
                y_pos += RM_LINE_HEIGHT  # Add extra space after headings
            
            elif item_type == "list":
                list_items = item.get("items", [])
                list_type = item.get("list_type", "ul")
                
                hcl_content += f'puts "set_font Lines {RM_BODY_SIZE}"\n'
                
                for i, list_item in enumerate(list_items):
                    y_pos += RM_LINE_HEIGHT
                    prefix = f"{i+1}. " if list_type == "ol" else "• "
                    item_text = sanitize_text(list_item)
                    
                    # Handle wrapping for list items
                    wrapped_text = textwrap.wrap(item_text, width=65)  # Narrower to account for bullet/number
                    
                    if wrapped_text:
                        # First line has the bullet/number
                        hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{prefix}{wrapped_text[0]}\\""\n'
                        
                        # Subsequent lines are indented
                        for line in wrapped_text[1:]:
                            y_pos += RM_LINE_HEIGHT
                            hcl_content += f'puts "text {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
            
            elif item_type == "blockquote":
                quote_text = sanitize_text(item.get("content", ""))
                
                y_pos += RM_LINE_HEIGHT
                hcl_content += f'puts "set_font Lines-Italic {RM_BODY_SIZE}"\n'
                
                # Wrap and indent blockquotes
                wrapped_quote = textwrap.wrap(quote_text, width=65)
                for line in wrapped_quote:
                    hcl_content += f'puts "text {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
                    y_pos += RM_LINE_HEIGHT
            
            elif item_type == "code":
                code_text = sanitize_text(item.get("content", ""))
                
                y_pos += RM_LINE_HEIGHT
                hcl_content += f'puts "set_font LinesMono {RM_CODE_SIZE}"\n'
                
                # Handle code blocks with line breaks
                code_lines = code_text.split('\n')
                for line in code_lines:
                    hcl_content += f'puts "text {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
                    y_pos += RM_LINE_HEIGHT
            
            elif item_type == "image" and item.get("image_id") in image_paths:
                # Handle images that were successfully downloaded
                img_id = item.get("image_id")
                img_path = image_paths[img_id]
                img_alt = sanitize_text(item.get("alt", "Image"))
                
                # Add some space before the image
                y_pos += RM_LINE_HEIGHT
                
                # Calculate image dimensions (keeping aspect ratio)
                max_width = RM_WIDTH - (2 * RM_MARGIN)
                img_width = min(500, max_width)  # Limit width to 500px or available width
                
                try:
                    with Image.open(img_path) as img:
                        aspect_ratio = img.height / img.width
                        img_height = int(img_width * aspect_ratio)
                except Exception as e:
                    print(f"Error calculating image dimensions: {e}")
                    img_height = img_width  # Fallback to square
                
                # Add the image
                hcl_content += f'puts "image {RM_MARGIN} {y_pos} {img_width} {img_height} \\"{img_path}\\""\n'
                
                # Update y position to after the image
                y_pos += img_height + RM_LINE_HEIGHT
                
                # Add image caption/alt text
                if img_alt:
                    hcl_content += f'puts "set_font Lines-Italic {RM_BODY_SIZE - 2}"\n'
                    hcl_content += f'puts "text {RM_MARGIN} {y_pos} \\"{img_alt}\\""\n'
                    y_pos += RM_LINE_HEIGHT
        
        # Create file
        hcl_filename = f"rm_{hash(url)}_{int(time.time())}.hcl"
        hcl_path = os.path.join(TEMP_DIR, hcl_filename)
        
        with open(hcl_path, 'w') as f:
            f.write(hcl_content)
        
        print(f"Created HCL file with {hcl_content.count('puts')} drawing commands")
        return hcl_path
    except Exception as e:
        print(f"Error creating HCL script: {e}")
        return None

def create_rmdoc_with_hcl(hcl_path, url):
    """
    Convert HCL directly to editable Remarkable Pro format.
    
    This function now:
    1. Converts the HCL directly to RM format with Remarkable Pro resolution
    2. Optimizes for Remarkable Pro with higher resolution (-r229)
    3. Allows headings to use non-Lines fonts that can be filled in manually
    """
    try:
        # Create RM file directly from HCL
        rm_filename = f"rm_{hash(url)}_{int(time.time())}.rm"
        rm_path = os.path.join(TEMP_DIR, rm_filename)
        
        # Convert HCL to RM format using drawj2d with Remarkable Pro resolution
        # Note: Current drawj2d creates v5 files but they're compatible with Remarkable Pro
        # The key is using Lines font family which ensures proper filled characters
        cmd = [DRAWJ2D_PATH, "-Trm", "-r229", "-o", rm_path, hcl_path]
        print(f"Converting HCL to RM format for Remarkable Pro: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error converting to RM format: {result.stderr}")
            # Try creating a RMDOC package from the HCL
            return create_rmdoc_from_hcl(hcl_path, url)
        
        # Verify the file exists and has content
        if not os.path.exists(rm_path):
            print(f"Error: RM file was not created at {rm_path}")
            return None
            
        # Check file size - Remarkable RM files should be at least 50 bytes (header)
        file_size = os.path.getsize(rm_path)
        if file_size < 50:
            print(f"Warning: RM file exists but may be empty or corrupted (size: {file_size} bytes)")
            print(f"This is likely still valid as minimal RM files are around 51 bytes with just headers")
        
        print(f"Successfully created RM file for Remarkable Pro: {rm_path} (size: {file_size} bytes)")
        return rm_path
    
    except Exception as e:
        print(f"Error converting to RM format: {e}")
        # Try fallback methods
        try:
            # Try a high-resolution PDF as fallback which can still be annotated
            pdf_filename = f"rm_{hash(url)}_{int(time.time())}.pdf"
            pdf_path = os.path.join(TEMP_DIR, pdf_filename)
            
            # Use higher dpi for better resolution on Remarkable Pro
            cmd = [DRAWJ2D_PATH, "-Tpdf", "-dpi", "300", "-o", pdf_path, hcl_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                print(f"Created high-resolution PDF fallback: {pdf_path}")
                return pdf_path
        except Exception as pdf_error:
            print(f"PDF fallback also failed: {pdf_error}")
        
        return None

def create_rmdoc_from_hcl(hcl_path, url):
    """
    Create a RMDOC package (zip file with metadata) from HCL file.
    Optimized for Remarkable Pro with proper resolution and color support.
    This is a fallback if direct RM conversion fails.
    """
    try:
        from uuid import uuid4
        from zipfile import ZipFile
        from datetime import datetime
        import json
        
        # Create temporary RM file first - with Remarkable Pro resolution
        temp_rm = os.path.join(TEMP_DIR, f"temp_{int(time.time())}.rm")
        
        # Convert HCL to RM format with Remarkable Pro resolution (-r229)
        # Note: Current drawj2d creates v5 files but they're compatible with Remarkable Pro
        # The key is using Lines font family which ensures proper filled characters
        cmd = [DRAWJ2D_PATH, "-Trm", "-r229", "-o", temp_rm, hcl_path]
        print(f"Creating RM file for RMDOC with Remarkable Pro settings")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating temporary RM file: {result.stderr}")
            return None
        
        # Create RMDOC filename
        rmdoc_filename = f"rm_{hash(url)}_{int(time.time())}.rmdoc"
        rmdoc_path = os.path.join(TEMP_DIR, rmdoc_filename)
        
        # Generate UUIDs and metadata
        document_uuid = str(uuid4())
        page_uuid = str(uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        
        # Extract document title from URL
        from urllib.parse import urlparse
        url_parts = urlparse(url)
        doc_name = f"URL: {url_parts.netloc}{url_parts.path}"
        if len(doc_name) > 50:
            doc_name = doc_name[:47] + "..."
        
        # Create the RMDOC file (zip format with metadata)
        with ZipFile(rmdoc_path, 'w') as output_zip:
            # Define single page
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
                "visibleName": doc_name
            }, indent=4))
            
            # Write content file with Remarkable Pro dimensions
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
                "customZoomPageHeight": 2404,  # Remarkable Pro height
                "customZoomPageWidth": 1872,   # Remarkable Pro width
                "customZoomScale": 1,
                "documentMetadata": {},
                "extraMetadata": {
                    "LastActiveTool": "primary",
                    "LastBallpointv2Color": "Red",  # Pro supports color
                    "LastBallpointv2Size": "2",
                    "LastEraserColor": "Black",
                    "LastEraserSize": "2",
                    "LastEraserTool": "Eraser",
                    "LastHighlighterv2Color": "ArgbCode",
                    "LastHighlighterv2ColorCode": "4294951820",  # Yellow highlighter
                    "LastHighlighterv2Size": "1",
                    "LastPen": "Ballpointv2",
                    "LastPencilv2Color": "Red",
                    "LastPencilv2Size": "3",
                    "LastSelectionToolColor": "Black",
                    "LastSelectionToolSize": "2",
                    "SecondaryHighlighterv2Color": "ArgbCode",
                    "SecondaryHighlighterv2ColorCode": "4294962549",  # Blue highlighter
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
            
            # Add the RM file to the zip
            output_zip.write(temp_rm, f'{document_uuid}/{page_uuid}.rm')
        
        # Clean up temporary file
        if os.path.exists(temp_rm):
            os.unlink(temp_rm)
        
        print(f"Successfully created RMDOC file for Remarkable Pro: {rmdoc_path}")
        return rmdoc_path
        
    except Exception as e:
        print(f"Error creating RMDOC: {e}")
        return None

def upload_to_remarkable(doc_path, title):
    """Upload a document to Remarkable Cloud using rmapi."""
    try:
        # Create a safe filename with timestamp to avoid duplicates
        timestamp = time.strftime("%m%d_%H%M%S")
        safe_title = "".join([c if c.isalnum() or c in " .-_" else "_" for c in title])
        safe_title = f"{safe_title}_{timestamp}"
        safe_title = safe_title[:50]  # Limit length
        
        # Determine file extension
        file_ext = os.path.splitext(doc_path)[1].lower()
        if not file_ext:
            file_ext = ".pdf"  # Default to PDF
        
        # Create a temporary copy of the file with the desired name
        temp_dir = os.path.dirname(doc_path)
        new_filename = f"{safe_title}{file_ext}"
        new_path = os.path.join(temp_dir, new_filename)
        
        # Copy the file to the new name
        import shutil
        shutil.copy2(doc_path, new_path)
        print(f"Created copy of file as {new_path}")
        
        # Upload using rmapi
        cmd = [RMAPI_PATH, "put", new_path, RM_FOLDER]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error uploading to Remarkable: {result.stderr}")
            return False, result.stderr
        
        print(f"Successfully uploaded to Remarkable Cloud as {safe_title}: {result.stdout}")
        return True, result.stdout
    except Exception as e:
        print(f"Exception uploading to Remarkable: {e}")
        return False, str(e)

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/share':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                # Try decoding as JSON first
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    url_to_share = data.get('url')
                except json.JSONDecodeError:
                    # Fallback: assume plain text URL if JSON fails
                    url_to_share = post_data.decode('utf-8').strip()

                if not url_to_share or not url_to_share.startswith(('http://', 'https://')):
                    raise ValueError("Invalid or missing URL")

                print(f"Received URL: {url_to_share}")

                # Generate QR Code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url_to_share)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")

                # Save QR Code image
                filename = f"qr_{hash(url_to_share)}.png"
                filepath = os.path.join(QR_OUTPUT_PATH, filename)
                img.save(filepath)
                print(f"QR Code saved to: {filepath}")
                
                # Check if the URL is a PDF
                is_pdf = is_pdf_url(url_to_share)
                print(f"URL is PDF: {is_pdf}")
                
                rmdoc_path = None
                webpage_content = {"title": "URL Content", "structured_content": [], "images": []}
                hcl_path = None
                
                if is_pdf:
                    # Process PDF URL
                    print(f"Processing PDF URL: {url_to_share}")
                    rmdoc_path = process_pdf_url(url_to_share, filepath)
                    
                    # Set webpage content with PDF title for response
                    title = "PDF Document"
                    try:
                        # Try to extract title from URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url_to_share)
                        path_parts = parsed_url.path.split('/')
                        if path_parts and path_parts[-1]:
                            title = os.path.splitext(path_parts[-1])[0].replace('_', ' ').replace('-', ' ')
                    except:
                        pass
                    
                    webpage_content = {
                        "title": f"PDF: {title}",
                        "structured_content": [{
                            "type": "paragraph",
                            "content": f"Extracted content from PDF: {url_to_share}"
                        }],
                        "images": []
                    }
                else:
                    # Scrape regular webpage content
                    print(f"Scraping content from: {url_to_share}")
                    webpage_content = scrape_webpage(url_to_share)
                    
                    # Create HCL script for Remarkable document
                    print(f"Creating HCL script for content and QR code")
                    hcl_path = create_hcl_script(url_to_share, filepath, webpage_content)
                    
                    # Convert HCL to Remarkable document format
                    if hcl_path:
                        print(f"Converting HCL to Remarkable document format")
                        rmdoc_path = create_rmdoc_with_hcl(hcl_path, url_to_share)
                    else:
                        print("Failed to create HCL script, skipping conversion")
                
                # Upload to Remarkable Cloud
                remarkable_status = {"uploaded": False, "message": "Skipped Remarkable upload"}
                
                if rmdoc_path:
                    print(f"Uploading Remarkable document to Remarkable Cloud")
                    success, message = upload_to_remarkable(rmdoc_path, webpage_content["title"])
                    remarkable_status = {
                        "uploaded": success,
                        "message": message
                    }
                else:
                    print("Failed to create Remarkable document, skipping upload")

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Verify the RM document was created successfully
                if rmdoc_path and os.path.exists(rmdoc_path):
                    rmdoc_status = rmdoc_path
                    file_size = os.path.getsize(rmdoc_path)
                    print(f"RM document exists with size: {file_size} bytes")
                    # 51 bytes is a valid RM file with just the header
                    if file_size == 51:
                        print(f"Valid RM file with header only ({file_size} bytes)")
                    elif file_size < 50:
                        print(f"Warning: Small RM file ({file_size} bytes), but might still be valid")
                else:
                    # Check if there's an RM file with the same base name
                    if rmdoc_path:
                        base_name = os.path.splitext(os.path.basename(rmdoc_path))[0]
                        for f in os.listdir(TEMP_DIR):
                            if f.startswith(base_name) and f.endswith('.rm'):
                                rm_path = os.path.join(TEMP_DIR, f)
                                print(f"Found alternative RM file: {rm_path}")
                                rmdoc_status = rm_path
                                break
                        else:
                            rmdoc_status = "Failed to create Remarkable document"
                            print("RM document does not exist or is invalid")
                    else:
                        rmdoc_status = "Failed to create Remarkable document"
                        print("No RM document path provided")
                
                response = {
                    'status': 'success',
                    'url_received': url_to_share,
                    'qr_path': filepath,
                    'hcl_path': hcl_path if hcl_path else "Failed to create HCL script",
                    'rmdoc_path': rmdoc_status,
                    'title': webpage_content["title"],
                    'remarkable': remarkable_status
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except Exception as e:
                print(f"Error processing request: {e}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }).encode('utf-8')
                )
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

def run(server_class=HTTPServer, handler_class=RequestHandler, port=LISTEN_PORT):
    server_address = (LISTEN_HOST, port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on {LISTEN_HOST}:{port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Stopping httpd server...")

if __name__ == '__main__':
    run()