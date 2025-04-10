"""Document creation service for Pi Share Receiver.

This service converts web content to reMarkable-compatible documents
using drawj2d to generate native reMarkable ink files.
"""

import os
import time
import json
import logging
import markdown
from bs4 import BeautifulSoup
import subprocess
import tempfile
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class DocumentService:
    """Creates reMarkable documents from web content."""
    
    def __init__(self, temp_dir: str, drawj2d_path: str):
        """Initialize with directories and paths.
        
        Args:
            temp_dir: Directory for temporary files
            drawj2d_path: Path to drawj2d executable
        """
        self.temp_dir = temp_dir
        self.drawj2d_path = drawj2d_path
        os.makedirs(temp_dir, exist_ok=True)
        
        # Font configuration
        self.heading_font = "Liberation Sans"  # Mid-century modern sans-serif font
        self.body_font = "Liberation Sans"
        self.code_font = "DejaVu Sans Mono"
        
        # Remarkable Pro page size (portrait mode)
        self.page_width = 1872
        self.page_height = 2404
        self.margin = 100

    def create_hcl(self, url: str, qr_path: str, content: Dict[str, Any]) -> Optional[str]:
        """Create HCL script from web content."""
        try:
            logger.info(f"Creating HCL document for: {content.get('title', url)}")
            
            # Generate HCL file path
            hcl_filename = f"doc_{hash(url)}.hcl"
            hcl_path = os.path.join(self.temp_dir, hcl_filename)
            
            with open(hcl_path, 'w', encoding='utf-8') as f:
                # Set title position
                y_pos = self.margin
                
                # Add title
                title = content.get('title', 'Untitled Document')
                f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(title)}"\n')
                y_pos += 60  # Extra spacing after title
                
                # Add URL under title
                f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(url)}"\n')
                y_pos += 40
                
                # Add QR code if available
                if os.path.exists(qr_path):
                    f.write(f'image_file "{qr_path}" {self.margin} {y_pos} 600 600\n')
                    y_pos += 640  # Image height + padding
                
                # Process content
                plain_content = self._process_content(content)
                
                # Split text into paragraphs and add to HCL
                paragraphs = plain_content.split('\n\n')
                for para in paragraphs:
                    if not para.strip():
                        continue
                    
                    # Check if we need a new page
                    if y_pos > (self.page_height - self.margin):
                        y_pos = self.margin
                    # Write the paragraph
                    if para.startswith('#'):  # Handle headings
                        f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(para.lstrip("#").strip())}"\n')
                        y_pos += 60  # Extra spacing after heading
                    else:
                        f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(para)}"\n')
                        y_pos += 40  # Standard spacing for paragraphs
                
                # Add timestamp at the bottom
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f'text {self.margin} {self.page_height - self.margin} "Generated: {timestamp}"\n')
            
            logger.info(f"Created HCL file: {hcl_path}")
            return hcl_path
        except Exception as e:
            logger.error(f"Error creating HCL document: {e}")
            return None

    def create_pdf_hcl(self, pdf_path: str, title: str, qr_path: str = None) -> Optional[str]:
        """Create HCL script for PDF file."""
        try:
            logger.info(f"Creating HCL document for PDF: {pdf_path}")
            
            # Generate HCL file path
            hcl_filename = f"pdf_{hash(pdf_path)}.hcl"
            hcl_path = os.path.join(self.temp_dir, hcl_filename)
            
            with open(hcl_path, 'w', encoding='utf-8') as f:
                # Add comment
                f.write(f'// PDF document: {os.path.basename(pdf_path)}\n\n')
                
                # Set initial position
                y_pos = self.margin
                
                # Add title
                f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(title)}"\n')
                y_pos += 60  # Extra spacing after title
                
                # Add QR code if available
                if qr_path and os.path.exists(qr_path):
                    f.write(f'image_file "{qr_path}" {self.margin} {y_pos} 600 600\n')
                    y_pos += 640  # Image height + padding
                
                # Add PDF content reference
                f.write(f'text {self.margin} {y_pos} "See original file: {os.path.basename(pdf_path)}"\n')
            
            logger.info(f"Created HCL file for PDF: {hcl_path}")
            return hcl_path
        except Exception as e:
            logger.error(f"Error creating HCL document for PDF: {e}")
            return None

    def create_from_markdown(self, markdown_text: str, title: str) -> Optional[str]:
        """Convert markdown to Remarkable document."""
        try:
            # Convert markdown to HTML
            html = markdown.markdown(markdown_text)
            # Convert HTML to plain text
            text = self._html_to_text(html)
            
            # Create temporary HCL file
            hcl_filename = f"markdown_{int(time.time())}.hcl"
            hcl_path = os.path.join(self.temp_dir, hcl_filename)
            
            # Split text into paragraphs
            paragraphs = text.split('\n\n')
            
            with open(hcl_path, 'w', encoding='utf-8') as f:
                # Add comment
                f.write('// Markdown document conversion\n\n')
                
                # Add title
                y_pos = self.margin
                f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(title)}"\n')
                y_pos += 60  # Extra spacing after title
                
                # Process paragraphs
                for para in paragraphs:
                    if not para.strip():
                        continue
                        
                    # Check if we need a new page
                    if y_pos > (self.page_height - self.margin):
                        y_pos = self.margin  # Reset y position instead of new_page
                    
                    # Handle heading-like paragraphs
                    if para.startswith('#'):
                        f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(para.lstrip("#").strip())}"\n')
                        y_pos += 60  # Extra spacing after heading
                    else:
                        f.write(f'text {self.margin} {y_pos} "{self._escape_hcl(para)}"\n')
                        y_pos += 40  # Standard spacing for paragraphs
            
            # Convert HCL to Remarkable document
            rm_filename = f"markdown_{int(time.time())}.rmdoc"
            rm_path = os.path.join(self.temp_dir, rm_filename)
            
            return self._convert_to_remarkable(hcl_path, rm_path)
        except Exception as e:
            logger.error(f"Error converting markdown to Remarkable: {e}")
            return None

    def create_rmdoc(self, hcl_path: str, url: str) -> Optional[str]:
        """Convert HCL to Remarkable document."""
        timestamp = int(time.time())
        rm_filename = f"rm_{hash(url)}_{timestamp}.rmdoc"
        rm_path = os.path.join(self.temp_dir, rm_filename)
        
        return self._convert_to_remarkable(hcl_path, rm_path)

    def _process_content(self, content: Dict[str, Any]) -> str:
        """Process content dictionary into plain text.
        
        Args:
            content: Dictionary containing either structured_content or raw content
            
        Returns:
            Processed plain text with proper formatting
        """
        plain_content = ""
        structured_content = content.get('structured_content', [])
        
        if structured_content:
            for item in structured_content:
                content_type = item.get('type', 'paragraph')
                text = item.get('content', '')
                
                if content_type == 'heading':
                    plain_content += f"{text}\n\n"  # No markdown-style heading
                elif content_type == 'paragraph':
                    plain_content += f"{text}\n\n"
                elif content_type == 'code':
                    plain_content += f"{text}\n\n"  # No code block markers
        else:
            plain_content = content.get('content', '')
            if plain_content and '<' in plain_content and '>' in plain_content:
                plain_content = self._html_to_text(plain_content)
        
        return plain_content

    def _convert_to_remarkable(self, hcl_path: str, rm_path: str) -> Optional[str]:
        """Convert HCL file to Remarkable format."""
        if not os.path.exists(hcl_path):
            logger.error(f"HCL file not found: {hcl_path}")
            return None
                
        if not os.path.exists(self.drawj2d_path):
            logger.error(f"drawj2d not found at {self.drawj2d_path}")
            return None
        
        cmd = [self.drawj2d_path, hcl_path, "-o", rm_path, "-T", "rm"]
        
        logger.info(f"Running drawj2d conversion: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(rm_path):
            logger.info(f"Created Remarkable document: {rm_path}")
            return rm_path
        else:
            logger.error(f"drawj2d error (code {result.returncode}): {result.stderr}")
            logger.error(f"Command attempted: {' '.join(cmd)}")
            return None

    def _escape_hcl(self, text: str) -> str:
        """Escape special characters for HCL."""
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

    def _html_to_text(self, html_content: str) -> str:
        """Extract text content from HTML, preserving structure."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.extract()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines and join with double newlines for paragraphs
            return '\n\n'.join(chunk for chunk in chunks if chunk)
        except Exception as e:
            logger.error(f"Error converting HTML to text: {e}")
            return html_content
