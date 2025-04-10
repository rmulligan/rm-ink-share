#!/usr/bin/env python3
"""
Pi Share Receiver Server

Receives URLs via HTTP POST, processes them, and uploads to Remarkable Pro.
"""

import os
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional, Tuple
import time

# Import configuration module
from config import CONFIG, setup_logging

# Import service implementations
from services.qr_service import QRCodeService
from services.pdf_service import PDFService
from services.web_scraper_service import WebScraperService
from services.document_service import DocumentService
from services.remarkable_service import RemarkableService

# Set up logging
logger = setup_logging()

class URLHandler(BaseHTTPRequestHandler):
    """Handler for URL sharing requests."""
    
    def setup(self):
        """Set up the handler after the parent is initialized."""
        # First initialize the parent
        super().setup()
        
        # Then initialize services safely
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize service instances safely."""
        try:
            self.qr_service = QRCodeService(CONFIG['TEMP_DIR'])
            self.pdf_service = PDFService(CONFIG['TEMP_DIR'], CONFIG['OUTPUT_DIR'])
            self.web_scraper = WebScraperService(CONFIG['TEMP_DIR'])
            self.document_service = DocumentService(CONFIG['TEMP_DIR'], CONFIG['DRAWJ2D_PATH'])
            self.remarkable_service = RemarkableService(CONFIG['RMAPI_PATH'], CONFIG['RM_FOLDER'])
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            logger.error(traceback.format_exc())
    
    def do_POST(self):
        """Handle POST request with URL to process."""
        if self.path != '/share':
            self._send_error("Invalid endpoint. Use /share")
            return
            
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error("Empty request")
                return
                
            # Read request body
            post_data = self.rfile.read(content_length)
            url = self._extract_url(post_data)
            
            if not url:
                self._send_error("No valid URL found")
                return
                
            logger.info(f"Processing URL: {url}")
            
            # Generate QR code
            qr_path, qr_filename = self.qr_service.generate_qr(url)
            logger.info(f"Generated QR code: {qr_filename}")
            
            # Process URL based on type
            if self.pdf_service.is_pdf_url(url):
                self._handle_pdf_url(url, qr_path)
            else:
                self._handle_webpage_url(url, qr_path)
                
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            self._send_error(f"Error processing request: {str(e)}")
    
    def _extract_url(self, post_data):
        """Extract URL from request data (JSON or plain text)."""
        # Try to decode as JSON
        try:
            data = json.loads(post_data.decode('utf-8'))
            url = data.get('url')
            if url and url.startswith(('http://', 'https://')):
                return url
        except json.JSONDecodeError:
            pass
            
        # Try as plain text
        try:
            text = post_data.decode('utf-8').strip()
            if text.startswith(('http://', 'https://')):
                return text
        except UnicodeDecodeError:
            pass
            
        return None
    
    def _handle_pdf_url(self, url, qr_path):
        """Handle PDF URL processing."""
        try:
            # Process PDF
            result = self.pdf_service.process_pdf(url, qr_path)
            if not result:
                self._send_error("Failed to process PDF")
                return
            
            # Create HCL for the PDF instead of uploading directly
            hcl_path = self.document_service.create_pdf_hcl(
                result["pdf_path"],
                result["title"],
                qr_path
            )
            
            if not hcl_path:
                self._send_error("Failed to create HCL script for PDF")
                return
                
            # Convert to Remarkable document
            rm_path = self.document_service.create_rmdoc(hcl_path, url)
            if not rm_path:
                self._send_error("Failed to convert PDF to Remarkable format")
                return
                
            # Upload to Remarkable
            success, message = self.remarkable_service.upload(
                rm_path, 
                result["title"]
            )
            
            if success:
                self._send_success(f"PDF uploaded to Remarkable as native ink: {result['title']}")
            else:
                self._send_error(f"Failed to upload PDF: {message}")
                
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            logger.error(traceback.format_exc())
            self._send_error(f"Error processing PDF: {str(e)}")
    
    def _handle_webpage_url(self, url, qr_path):
        """Handle webpage URL processing."""
        try:
            # Scrape content
            content = self.web_scraper.scrape(url)
            
            # Create HCL script
            hcl_path = self.document_service.create_hcl(url, qr_path, content)
            if not hcl_path:
                self._send_error("Failed to create HCL script")
                return
                
            # Convert to Remarkable document
            rm_path = self.document_service.create_rmdoc(hcl_path, url)
            if not rm_path:
                self._send_error("Failed to convert to Remarkable format")
                return
                
            # Upload to Remarkable
            success, message = self.remarkable_service.upload(
                rm_path,
                content["title"]
            )
            
            if success:
                self._send_success(f"Webpage uploaded to Remarkable: {content['title']}")
            else:
                self._send_error(f"Failed to upload document: {message}")
                
        except Exception as e:
            logger.error(f"Error processing webpage: {str(e)}")
            logger.error(traceback.format_exc())
            self._send_error(f"Error processing webpage: {str(e)}")
    
    def _send_success(self, message):
        """Send success response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = json.dumps({
            "success": True,
            "message": message
        })
        
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, message):
        """Send error response."""
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = json.dumps({
            "success": False,
            "error": message
        })
        
        self.wfile.write(response.encode('utf-8'))

def main():
    """Start the HTTP server."""
    try:
        # Ensure directories exist
        os.makedirs(CONFIG['TEMP_DIR'], exist_ok=True)
        os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
        
        # Create server
        server = HTTPServer((CONFIG['HOST'], CONFIG['PORT']), URLHandler)
        logger.info(f"Server started at http://{CONFIG['HOST']}:{CONFIG['PORT']}")
        
        # Serve until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        if 'server' in locals():
            server.server_close()
        logger.info("Server stopped")

if __name__ == "__main__":
    main()