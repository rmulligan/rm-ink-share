import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional

from services.interfaces import (
    IQRCodeService,
    IPDFService,
    IWebScraperService,
    IDocumentService,
    IRemarkableService
)
from services.qr_service import QRCodeService
from services.pdf_service import PDFService
from services.web_scraper_service import WebScraperService
from services.document_service import DocumentService
from services.remarkable_service import RemarkableService

# Configuration
CONFIG = {
    'HOST': '0.0.0.0',
    'PORT': 8000,
    'TEMP_DIR': '../temp',
    'OUTPUT_DIR': '../output',
    'RMAPI_PATH': '/usr/local/bin/rmapi',
    'RM_FOLDER': '/',
    'DRAWJ2D_PATH': '/usr/local/bin/drawj2d',
}

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, 
                 qr_service: IQRCodeService,
                 pdf_service: IPDFService,
                 web_scraper: IWebScraperService,
                 document_service: IDocumentService,
                 remarkable_service: IRemarkableService,
                 *args, **kwargs):
        self.qr_service = qr_service
        self.pdf_service = pdf_service
        self.web_scraper = web_scraper
        self.document_service = document_service
        self.remarkable_service = remarkable_service
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """Handle POST request with URL to process"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            url = data.get('url')

            if not url:
                self._send_error("No URL provided")
                return

            # Generate QR code
            qr_path, qr_filename = self.qr_service.generate_qr(url)

            # Process URL based on type
            if self.pdf_service.is_pdf_url(url):
                self._handle_pdf_url(url, qr_path)
            else:
                self._handle_webpage_url(url, qr_path)

        except Exception as e:
            self._send_error(f"Error processing request: {str(e)}")

    def _handle_pdf_url(self, url: str, qr_path: str):
        """Handle PDF URL"""
        try:
            # Process PDF
            result = self.pdf_service.process_pdf(url, qr_path)
            if not result:
                self._send_error("Failed to process PDF")
                return

            # Upload to Remarkable
            success, message = self.remarkable_service.upload(result["pdf_path"], result["title"])
            
            if success:
                self._send_success("PDF processed and uploaded successfully")
            else:
                self._send_error(f"Failed to upload PDF: {message}")

        except Exception as e:
            self._send_error(f"Error processing PDF: {str(e)}")

    def _handle_webpage_url(self, url: str, qr_path: str):
        """Handle webpage URL"""
        try:
            # Scrape content
            content = self.web_scraper.scrape(url)
            
            # Create HCL script
            hcl_path = self.document_service.create_hcl(url, qr_path, content)
            if not hcl_path:
                self._send_error("Failed to create HCL script")
                return

            # Convert to RM document
            rm_path = self.document_service.create_rmdoc(hcl_path, url)
            if not rm_path:
                self._send_error("Failed to convert to RM format")
                return

            # Upload to Remarkable
            success, message = self.remarkable_service.upload(rm_path, content["title"])
            
            if success:
                self._send_success("Webpage processed and uploaded successfully")
            else:
                self._send_error(f"Failed to upload document: {message}")

        except Exception as e:
            self._send_error(f"Error processing webpage: {str(e)}")

    def _send_success(self, message: str):
        """Send success response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"success": True, "message": message})
        self.wfile.write(response.encode())

    def _send_error(self, message: str):
        """Send error response"""
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"success": False, "error": message})
        self.wfile.write(response.encode())

class CustomHTTPServer(HTTPServer):
    def __init__(self, server_address, services):
        self.services = services
        super().__init__(server_address, self._handler_with_services)

    def _handler_with_services(self, *args, **kwargs):
        handler = RequestHandler(*args, **kwargs)
        for service_name, service in self.services.items():
            setattr(handler, service_name, service)
        return handler

def main():
    # Create directories
    os.makedirs(CONFIG['TEMP_DIR'], exist_ok=True)
    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)

    # Initialize services
    services = {
        'qr_service': QRCodeService(CONFIG['TEMP_DIR']),
        'pdf_service': PDFService(CONFIG['TEMP_DIR'], CONFIG['OUTPUT_DIR']),
        'web_scraper': WebScraperService(CONFIG['TEMP_DIR']),
        'document_service': DocumentService(CONFIG['TEMP_DIR'], CONFIG['DRAWJ2D_PATH']),
        'remarkable_service': RemarkableService(CONFIG['RMAPI_PATH'], CONFIG['RM_FOLDER'])
    }

    # Start server with services
    server = CustomHTTPServer((CONFIG['HOST'], CONFIG['PORT']), services)
    print(f"Server started at http://{CONFIG['HOST']}:{CONFIG['PORT']}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Server stopped")

if __name__ == "__main__":
    main()