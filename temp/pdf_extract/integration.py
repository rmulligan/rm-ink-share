#!/usr/bin/env python3
"""
Integration module for PDF extraction with Pi Share Receiver.

This module provides functions to integrate the PDF extraction tools
with the Pi Share Receiver server for handling PDF content.
"""

import os
import sys
import tempfile
import time
import requests
import subprocess
from urllib.parse import urlparse
from extract_pdf_text import extract_text_from_pdf, create_remarkable_hcl
from pdf_to_remarkable import create_rm_file, create_rmdoc_package

def download_pdf(url, output_path=None):
    """
    Download a PDF file from a URL.
    
    Args:
        url: The URL of the PDF file to download
        output_path: Optional path to save the PDF file
        
    Returns:
        Path to the downloaded PDF file
    """
    if output_path is None:
        # Create a temporary file for the PDF
        fd, output_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Check if the response is a PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
            print(f"Warning: URL does not appear to be a PDF (Content-Type: {content_type})")
        
        # Save the PDF
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded PDF from {url} to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error downloading PDF from {url}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def process_pdf_url(url, output_dir=None, resolution=229):
    """
    Process a PDF URL for Remarkable.
    
    Downloads a PDF from the URL and converts it to Remarkable format.
    
    Args:
        url: The URL of the PDF to process
        output_dir: Directory to save output files
        resolution: Resolution for the RM file
        
    Returns:
        Tuple of (rmdoc_path, rm_path) or (None, None) on failure
    """
    # Set up output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse URL to get a base name for output files
    parsed_url = urlparse(url)
    base_name = os.path.basename(parsed_url.path)
    if not base_name or not base_name.lower().endswith('.pdf'):
        base_name = f"pdf_extract_{int(time.time())}.pdf"
    else:
        base_name = base_name.replace('%20', '_').replace(' ', '_')
    
    # Strip the .pdf extension
    base_name = os.path.splitext(base_name)[0]
    
    # Download the PDF
    pdf_path = download_pdf(url)
    
    if not pdf_path:
        return None, None
    
    try:
        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            print(f"No text extracted from {pdf_path}")
            return None, None
        
        # Create output paths
        hcl_path = os.path.join(output_dir, f"{base_name}.hcl")
        rm_path = os.path.join(output_dir, f"{base_name}.rm")
        rmdoc_path = os.path.join(output_dir, f"{base_name}.rmdoc")
        
        # Create HCL script
        create_remarkable_hcl(text, output_path=hcl_path, title=base_name)
        
        # Create RM file
        create_rm_file(hcl_path, output_path=rm_path, resolution=resolution)
        
        # Create RMDOC package
        create_rmdoc_package(rm_path, output_path=rmdoc_path, title=base_name)
        
        print(f"Processed PDF from {url}")
        print(f"- RM file: {rm_path}")
        print(f"- RMDOC package: {rmdoc_path}")
        
        return rmdoc_path, rm_path
    
    except Exception as e:
        print(f"Error processing PDF from {url}: {e}")
        return None, None
    
    finally:
        # Clean up the downloaded PDF
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

def server_integration_example():
    """Example of how to integrate with the Pi Share Receiver server."""
    # This is a simplified example to show the integration pattern
    
    def handle_pdf_url(url, output_dir):
        """Handle a PDF URL in the server context."""
        print(f"Processing PDF URL: {url}")
        
        # Process the PDF URL
        rmdoc_path, rm_path = process_pdf_url(url, output_dir=output_dir)
        
        if not rmdoc_path:
            return {
                "success": False,
                "error": "Failed to process PDF"
            }
        
        # In the actual server, you would:
        # 1. Upload the RMDOC file to the Remarkable cloud
        # 2. Or provide the file for download
        # 3. Or display a QR code for the file
        
        return {
            "success": True,
            "rmdoc_path": rmdoc_path,
            "rm_path": rm_path
        }
    
    # Example usage
    pdf_url = "https://example.com/document.pdf"
    output_dir = "/path/to/output/directory"
    
    result = handle_pdf_url(pdf_url, output_dir)
    
    if result["success"]:
        print(f"PDF processed successfully:")
        print(f"- RMDOC: {result['rmdoc_path']}")
        print(f"- RM: {result['rm_path']}")
    else:
        print(f"PDF processing failed: {result.get('error', 'Unknown error')}")

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
        headers = requests.head(url, allow_redirects=True).headers
        content_type = headers.get('Content-Type', '').lower()
        
        return 'application/pdf' in content_type
    
    except Exception as e:
        print(f"Error checking if URL is PDF: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        pdf_url = sys.argv[1]
        
        # Check if the URL is a PDF
        if is_pdf_url(pdf_url):
            print(f"{pdf_url} appears to be a PDF. Processing...")
            rmdoc_path, rm_path = process_pdf_url(pdf_url, output_dir=".")
            
            if rmdoc_path:
                print(f"PDF processed successfully!")
        else:
            print(f"{pdf_url} does not appear to be a PDF.")
    else:
        print("Usage: python integration.py <pdf_url>")