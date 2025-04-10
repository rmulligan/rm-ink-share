import os
import time
import json
import uuid
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional
import textwrap
from PIL import Image
from .interfaces import IDocumentService

class DocumentService(IDocumentService):
    def __init__(self, temp_dir: str, drawj2d_path: str):
        self.temp_dir = temp_dir
        self.drawj2d_path = drawj2d_path
        self.config = {
            'RM_WIDTH': 1872,
            'RM_HEIGHT': 2404,
            'RM_MARGIN': 120,
            'RM_LINE_HEIGHT': 35,
            'RM_HEADER_LINE_HEIGHT': 55,
            'RM_TITLE_SIZE': 36,
            'RM_BODY_SIZE': 18,
            'RM_CODE_SIZE': 16
        }
        os.makedirs(temp_dir, exist_ok=True)

    def create_hcl(self, url: str, qr_path: str, content: Dict) -> Optional[str]:
        """Create HCL script from content"""
        try:
            title = self._sanitize_text(content.get("title", "Untitled"))
            structured_content = content.get("structured_content", [])
            images = content.get("images", [])
            
            # Download images
            image_paths = {}
            for img in images:
                img_path = self._download_image(img["src"], img["id"])
                if img_path:
                    image_paths[img["id"]] = img_path
            
            # Create HCL content
            hcl_content = self._generate_hcl_content(url, title, structured_content, qr_path, image_paths)
            
            # Save HCL file
            hcl_filename = f"rm_{hash(url)}_{int(time.time())}.hcl"
            hcl_path = os.path.join(self.temp_dir, hcl_filename)
            
            with open(hcl_path, 'w') as f:
                f.write(hcl_content)
            
            return hcl_path
            
        except Exception as e:
            print(f"Error creating HCL script: {e}")
            return None

    def create_rmdoc(self, hcl_path: str, url: str) -> Optional[str]:
        """Convert HCL to Remarkable document"""
        try:
            # Create RM file directly from HCL
            rm_filename = f"rm_{hash(url)}_{int(time.time())}.rm"
            rm_path = os.path.join(self.temp_dir, rm_filename)
            
            # Convert using drawj2d with Remarkable Pro settings
            cmd = [self.drawj2d_path, "-Trm", "-r229", "-o", rm_path, hcl_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error converting to RM format: {result.stderr}")
                return self._create_rmdoc_package(hcl_path, url)
            
            # Verify file exists and has content
            if not os.path.exists(rm_path) or os.path.getsize(rm_path) < 50:
                print(f"Error: RM file was not created properly at {rm_path}")
                return None
                
            return rm_path
            
        except Exception as e:
            print(f"Error converting to RM format: {e}")
            return None

    def _sanitize_text(self, text: str) -> str:
        """Clean text for HCL script"""
        if not text:
            return ""
        text = text.replace('"', '\\"')
        text = text.replace('\\', '\\\\')
        text = ''.join(c for c in text if c.isprintable() or c == '\n')
        return text

    def _generate_hcl_content(self, url: str, title: str, content: List[Dict], qr_path: str, image_paths: Dict) -> str:
        """Generate HCL script content"""
        hcl = [
            f'# Remarkable document for URL: {url}',
            f'# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}',
            '',
            f'puts "size {self.config["RM_WIDTH"]} {self.config["RM_HEIGHT"]}"',
            '',
            'puts "pen black"',
            'puts "line_width 1"',
            '',
            f'puts "set_font Lines {self.config["RM_TITLE_SIZE"]}"',
            f'puts "text {self.config["RM_MARGIN"]} {self.config["RM_MARGIN"]} \\"{title[:80]}\\""',
            '',
            f'puts "set_font Lines {self.config["RM_BODY_SIZE"]}"',
            f'puts "text {self.config["RM_MARGIN"]} {self.config["RM_MARGIN"] + self.config["RM_LINE_HEIGHT"] * 2} \\"Source: {url}\\""'
        ]

        # Add QR code
        if os.path.exists(qr_path):
            qr_size = 350
            qr_x = self.config["RM_WIDTH"] - self.config["RM_MARGIN"] - qr_size
            qr_y = self.config["RM_MARGIN"]
            hcl.append(f'puts "image {qr_x} {qr_y} {qr_size} {qr_size} \\"{qr_path}\\""')

        y_pos = self.config["RM_MARGIN"] + self.config["RM_LINE_HEIGHT"] * 5

        # Process content
        for item in content:
            y_pos = self._add_content_item(hcl, item, y_pos, image_paths)

        return '\n'.join(hcl)

    def _add_content_item(self, hcl: List[str], item: Dict, y_pos: int, image_paths: Dict) -> int:
        """Add a content item to HCL script and return new y_position"""
        item_type = item.get("type", "")
        content = item.get("content", "")

        if item_type == "paragraph":
            hcl.append(f'puts "set_font Lines {self.config["RM_BODY_SIZE"]}"')
            for line in textwrap.wrap(self._sanitize_text(content), width=70):
                y_pos += self.config["RM_LINE_HEIGHT"]
                hcl.append(f'puts "text {self.config["RM_MARGIN"]} {y_pos} \\"{line}\\""')
            y_pos += self.config["RM_LINE_HEIGHT"] / 2

        elif item_type.startswith("h"):
            level = int(item_type[1])
            size = self.config["RM_TITLE_SIZE"] - (level - 1) * 4
            y_pos += self.config["RM_HEADER_LINE_HEIGHT"]
            hcl.append(f'puts "set_font Lines {size}"')
            hcl.append(f'puts "text {self.config["RM_MARGIN"]} {y_pos} \\"{self._sanitize_text(content)}\\""')
            y_pos += self.config["RM_LINE_HEIGHT"]

        elif item_type == "image" and item.get("image_id") in image_paths:
            img_path = image_paths[item["image_id"]]
            y_pos += self.config["RM_LINE_HEIGHT"]
            width = min(500, self.config["RM_WIDTH"] - 2 * self.config["RM_MARGIN"])
            
            try:
                with Image.open(img_path) as img:
                    aspect_ratio = img.height / img.width
                    height = int(width * aspect_ratio)
            except Exception:
                height = width

            hcl.append(f'puts "image {self.config["RM_MARGIN"]} {y_pos} {width} {height} \\"{img_path}\\""')
            y_pos += height + self.config["RM_LINE_HEIGHT"]

        return y_pos

    def _create_rmdoc_package(self, hcl_path: str, url: str) -> Optional[str]:
        """Create a RMDOC package as fallback"""
        try:
            # Generate a RMDOC package
            rmdoc_filename = f"rm_{hash(url)}_{int(time.time())}.rmdoc"
            rmdoc_path = os.path.join(self.temp_dir, rmdoc_filename)
            
            document_uuid = str(uuid.uuid4())
            page_uuid = str(uuid.uuid4())
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # Create temporary RM file
            temp_rm = os.path.join(self.temp_dir, f"temp_{int(time.time())}.rm")
            result = subprocess.run(
                [self.drawj2d_path, "-Trm", "-r229", "-o", temp_rm, hcl_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or not os.path.exists(temp_rm):
                return None

            from zipfile import ZipFile
            with ZipFile(rmdoc_path, 'w') as output_zip:
                # Add metadata
                output_zip.writestr(f"{document_uuid}.metadata", json.dumps({
                    "visibleName": f"URL Document {time.strftime('%Y-%m-%d')}",
                    "type": "DocumentType",
                    "pages": [{"id": page_uuid}],
                    "lastModified": str(timestamp),
                    "lastOpened": str(timestamp),
                    "lastOpenedPage": 0,
                    "pageCount": 1,
                }))

                # Add content file
                output_zip.writestr(f"{document_uuid}.content", json.dumps({
                    "extraMetadata": {},
                    "fileType": "notebook",
                    "pageCount": 1,
                    "pages": [{"id": page_uuid}]
                }))

                # Add RM file
                output_zip.write(temp_rm, f'{document_uuid}/{page_uuid}.rm')

            # Cleanup
            if os.path.exists(temp_rm):
                os.unlink(temp_rm)

            return rmdoc_path

        except Exception as e:
            print(f"Error creating RMDOC package: {e}")
            return None

    def _download_image(self, url: str, img_id: str) -> Optional[str]:
        """Download an image and return its path"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            ext = 'jpg'
            if 'png' in content_type:
                ext = 'png'
            elif 'gif' in content_type:
                ext = 'gif'
            elif 'svg' in content_type:
                ext = 'svg'
            
            image_path = os.path.join(self.temp_dir, f"{img_id}.{ext}")
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return image_path
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return None