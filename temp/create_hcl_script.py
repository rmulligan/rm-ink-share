def create_hcl_script(url, qr_image_path, content):
    """Create an HCL script for drawj2d to generate a Remarkable document with editable content."""
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
        
        # Create HCL script using vector paths for text to ensure editability on device
        hcl_content = f"""# Remarkable document for URL: {url}
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}

puts "size {RM_WIDTH} {RM_HEIGHT}"

# Set up for vector paths (editable on device)
puts "line_width 1"
puts "line_color {RM_TEXT_COLOR}"

# Title
puts "set_font {RM_TITLE_FONT} {RM_TITLE_SIZE}"
puts "text_to_path {RM_MARGIN} {RM_MARGIN} \\"{title[:80]}\\""

# URL
puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"
puts "text_to_path {RM_MARGIN} {RM_MARGIN + RM_LINE_HEIGHT * 2} \\"Source: {url}\\""

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
                    hcl_content += f'puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"\n'
                    
                    # Wrap long paragraphs to prevent horizontal overflow
                    chunks = textwrap.wrap(content_text, width=70)
                    for chunk in chunks:
                        y_pos += RM_LINE_HEIGHT
                        hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"{sanitize_text(chunk)}\\""\n'
                    
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
                
                hcl_content += f'puts "set_font {RM_HEADING_FONT} {font_size}"\n'
                hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"{heading_text}\\""\n'
                y_pos += RM_LINE_HEIGHT  # Add extra space after headings
            
            elif item_type == "list":
                list_items = item.get("items", [])
                list_type = item.get("list_type", "ul")
                
                hcl_content += f'puts "set_font {RM_BODY_FONT} {RM_BODY_SIZE}"\n'
                
                for i, list_item in enumerate(list_items):
                    y_pos += RM_LINE_HEIGHT
                    prefix = f"{i+1}. " if list_type == "ol" else "• "
                    item_text = sanitize_text(list_item)
                    
                    # Handle wrapping for list items
                    wrapped_text = textwrap.wrap(item_text, width=65)  # Narrower to account for bullet/number
                    
                    if wrapped_text:
                        # First line has the bullet/number
                        hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"{prefix}{wrapped_text[0]}\\""\n'
                        
                        # Subsequent lines are indented
                        for line in wrapped_text[1:]:
                            y_pos += RM_LINE_HEIGHT
                            hcl_content += f'puts "text_to_path {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
            
            elif item_type == "blockquote":
                quote_text = sanitize_text(item.get("content", ""))
                
                y_pos += RM_LINE_HEIGHT
                hcl_content += f'puts "set_font {RM_BODY_FONT_ITALIC} {RM_BODY_SIZE}"\n'
                
                # Wrap and indent blockquotes
                wrapped_quote = textwrap.wrap(quote_text, width=65)
                for line in wrapped_quote:
                    hcl_content += f'puts "text_to_path {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
                    y_pos += RM_LINE_HEIGHT
            
            elif item_type == "code":
                code_text = sanitize_text(item.get("content", ""))
                
                y_pos += RM_LINE_HEIGHT
                hcl_content += f'puts "set_font {RM_CODE_FONT} {RM_CODE_SIZE}"\n'
                
                # Handle code blocks with line breaks
                code_lines = code_text.split('\n')
                for line in code_lines:
                    hcl_content += f'puts "text_to_path {RM_MARGIN + 20} {y_pos} \\"{sanitize_text(line)}\\""\n'
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
                    hcl_content += f'puts "set_font {RM_BODY_FONT_ITALIC} {RM_BODY_SIZE - 2}"\n'
                    hcl_content += f'puts "text_to_path {RM_MARGIN} {y_pos} \\"{img_alt}\\""\n'
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