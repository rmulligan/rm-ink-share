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

def create_hcl(self, url: str, qr_path: str, content: Dict[str, Any]) -> Optional[str]:
    """Create HCL script from web content."""
    try:
        # Ensure we have valid content, even if minimal
        if not content:
            content = {"title": f"Page from {url}", "structured_content": []}
            
        logger.info(f"Creating HCL document for: {content.get('title', url)}")
        
        # Generate HCL file path
        hcl_filename = f"doc_{hash(url)}.hcl"
        hcl_path = os.path.join(self.temp_dir, hcl_filename)
        
        with open(hcl_path, 'w', encoding='utf-8') as f:
            # Set page size - use direct syntax based on drawj2d docs
            f.write(f'puts "size {self.page_width} {self.page_height}"\n')
            f.write('puts "font \\"Lines\\""\n')
            f.write('puts "pen black"\n')
            
            # Log the HCL content being written
            logger.info(f"Writing HCL content to {hcl_path}")
            
            # Set title position
            y_pos = self.margin
            
            # Add title
            title = content.get('title', 'Untitled Document')
            f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(title)}\\""\n')
            y_pos += 60  # Extra spacing after title
            
            # Add URL under title
            f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(url)}\\""\n')
            y_pos += 40
            
            # Add QR code if available
            if os.path.exists(qr_path):
                f.write(f'puts "image_file \\"{qr_path}\\" {self.margin} {y_pos} 600 600"\n')
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
                    f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(para.lstrip("#").strip())}\\""\\n')
                    y_pos += 60  # Extra spacing after heading
                else:
                    f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(para)}\\""\\n')
                    y_pos += 40  # Standard spacing for paragraphs
            
            # Add timestamp at the bottom
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f'puts "text {self.margin} {self.page_height - self.margin} \\"Generated: {timestamp}\\""\n')
        
        logger.info(f"Created HCL file: {hcl_path}")
        return hcl_path
    except Exception as e:
        logger.error(f"Error creating HCL document: {e}")
        return None

import subprocess
import tempfile
from typing import Dict, Any, Optional, List

# Import configuration with proper relative import
try:
    from ..config import CONFIG
except ImportError:
    # Fallback to defaults if config cannot be imported
    CONFIG = {
        'PAGE_WIDTH': 1872,
        'PAGE_HEIGHT': 2404,
        'PAGE_MARGIN': 100,
        'HEADING_FONT': 'Liberation Sans',
        'BODY_FONT': 'Liberation Sans',
        'CODE_FONT': 'DejaVu Sans Mono'
    }

# Import utility functions for error handling
try:
    from ..utils import retry_operation, format_error
except ImportError:
    # If we can't import the utilities, define minimal versions
    def retry_operation(operation, *args, **kwargs):
        return operation(*args, **kwargs)
    
    def format_error(error_type, message, details=None):
        return f"{error_type}: {message}"

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
        
        # Font configuration from central config
        self.heading_font = CONFIG['HEADING_FONT']
        self.body_font = CONFIG['BODY_FONT']
        self.code_font = CONFIG['CODE_FONT']
        
        # Remarkable Pro page size (portrait mode) from central config
        self.page_width = CONFIG['PAGE_WIDTH']
        self.page_height = CONFIG['PAGE_HEIGHT']
        self.margin = CONFIG['PAGE_MARGIN']

    def create_hcl(self, url: str, qr_path: str, content: Dict[str, Any]) -> Optional[str]:
        """Create HCL script from web content."""
        try:
            # Ensure we have valid content, even if minimal
            if not content:
                content = {"title": f"Page from {url}", "structured_content": []}
                
            logger.info(f"Creating HCL document for: {content.get('title', url)}")
            
            # Generate HCL file path
            hcl_filename = f"doc_{hash(url)}.hcl"
            hcl_path = os.path.join(self.temp_dir, hcl_filename)
            
            with open(hcl_path, 'w', encoding='utf-8') as f:
                # Set page size - use direct syntax based on drawj2d docs
                f.write(f'puts "size {self.page_width} {self.page_height}"\n')
                f.write('puts "font \\"Lines\\""\n')
                f.write('puts "pen black"\n')
                
                # Set title position
                y_pos = self.margin
                
                # Add title
                title = content.get('title', 'Untitled Document')
                f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(title)}\\""\n')
                y_pos += 60  # Extra spacing after title
                
                # Add URL under title
                f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(url)}\\""\n')
                y_pos += 40
                
                # Add QR code if available
                if os.path.exists(qr_path):
                    f.write(f'puts "image_file \\"{qr_path}\\" {self.margin} {y_pos} 600 600"\n')
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
                        f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(para.lstrip("#").strip())}\\""\\n')
                        y_pos += 60  # Extra spacing after heading
                    else:
                        f.write(f'puts "text {self.margin} {y_pos} \\"{self._escape_hcl(para)}\\""\\n')
                        y_pos += 40  # Standard spacing for paragraphs
                
                # Add timestamp at the bottom
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f'puts "text {self.margin} {self.page_height - self.margin} \\"Generated: {timestamp}\\""\n')
            
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
        try:
            logger.info(f"Starting conversion from {hcl_path} to {rm_path}")
            print(f"DEBUG: Starting conversion from {hcl_path} to {rm_path}")
            
            # Input validation
            if not os.path.exists(hcl_path):
                error_msg = format_error("input", "HCL file not found", hcl_path)
                logger.error(error_msg)
                print(f"DEBUG ERROR: {error_msg}")
                return None
                    
            if not os.path.exists(self.drawj2d_path):
                error_msg = format_error("config", "drawj2d executable not found", self.drawj2d_path)
                logger.error(error_msg)
                print(f"DEBUG ERROR: {error_msg}")
                return None
            
            # Double check file contents
            try:
                with open(hcl_path, 'r') as f:
                    hcl_content = f.read()
                    logger.info(f"HCL file content (first 100 chars): {hcl_content[:100]}")
                    print(f"DEBUG: HCL file exists and is readable, size: {len(hcl_content)} bytes")
            except Exception as e:
                logger.error(f"Failed to read HCL file: {e}")
                print(f"DEBUG ERROR: Failed to read HCL file: {e}")
                
            # Check output path
            output_dir = os.path.dirname(rm_path)
            if not os.path.exists(output_dir):
                logger.info(f"Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
                
            # Use only the minimal flags that worked when we tested manually
            # -Trm: Target is Remarkable
            # -o: Specify output file
            cmd = [self.drawj2d_path, "-Trm", "-o", rm_path, hcl_path]
            logger.info(f"Conversion command: {' '.join(cmd)}")
            print(f"DEBUG: Running conversion: {' '.join(cmd)}")
            
            # Define the conversion function that will be retried if it fails
            def run_conversion(cmd_args):
                logger.info(f"Running drawj2d conversion: {' '.join(cmd_args)}")
                
                # Running the conversion using subprocess.run for better error handling
                result = subprocess.run(cmd_args, capture_output=True, text=True)
                logger.info(f"Command stdout: {result.stdout}")
                logger.info(f"Command stderr: {result.stderr}")
                
                if result.returncode != 0:
                    raise RuntimeError(f"drawj2d conversion failed: Exit code {result.returncode}, stderr: {result.stderr}")
                
                if not os.path.exists(rm_path):
                    logger.error(f"Output file missing: {rm_path}, even though command reported success")
                    raise FileNotFoundError(f"Expected output file not created: {rm_path}")
                else:
                    logger.info(f"Output file successfully created: {rm_path} ({os.path.getsize(rm_path)} bytes)")
                
                return rm_path
            
            # Use retry operation for running the conversion
            return retry_operation(
                run_conversion,
                cmd,
                operation_name="Document conversion",
                max_retries=2  # Only retry a couple of times for conversion
            )
                
        except Exception as e:
            logger.error(format_error("conversion", "Failed to convert document to Remarkable format", e))
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

