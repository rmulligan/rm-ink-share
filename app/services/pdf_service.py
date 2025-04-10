import os
import time
from urllib.parse import urlparse
import requests
import PyPDF2
from typing import Dict, Optional
from .interfaces import IPDFService

class PDFService(IPDFService):
    def __init__(self, temp_dir: str, extract_dir: str):
        self.temp_dir = temp_dir
        self.extract_dir = extract_dir
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(extract_dir, exist_ok=True)

    def is_pdf_url(self, url: str) -> bool:
        """Check if URL points to PDF file"""
        if url.lower().endswith('.pdf'):
            return True
        
        try:
            headers = requests.head(url, allow_redirects=True, timeout=10).headers
            content_type = headers.get('Content-Type', '').lower()
            return 'application/pdf' in content_type
        except Exception as e:
            print(f"Error checking if URL is PDF: {e}")
            return False

    def process_pdf(self, url: str, qr_path: str) -> Optional[str]:
        """Process PDF URL and return document path"""
        try:
            print(f"Processing PDF URL: {url}")
            
            # Download PDF
            pdf_filename = f"temp_pdf_{int(time.time())}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract metadata
            title = self._extract_pdf_title(pdf_path, url)
            content = self._extract_pdf_content(pdf_path)
            
            # Create structured content
            return {
                "title": title,
                "content": content,
                "pdf_path": pdf_path
            }
            
        except Exception as e:
            print(f"Error processing PDF URL: {e}")
            return None

    def _extract_pdf_title(self, pdf_path: str, url: str) -> str:
        """Extract title from PDF metadata or URL"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if reader.metadata and reader.metadata.title:
                    return reader.metadata.title
        except Exception:
            pass
        
        # Fallback to URL
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            if path_parts and path_parts[-1]:
                return os.path.splitext(path_parts[-1])[0].replace('_', ' ').replace('-', ' ')
        except Exception:
            pass
        
        return "PDF Document"

    def _extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = []
                for page in reader.pages:
                    content.append(page.extract_text())
                return "\n\n".join(content)
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return "PDF content extraction failed"