#!/usr/bin/env python3
"""
Create an annotatable PDF for Remarkable.

While not directly editable as text, this will allow annotations
and should display properly on the device.
"""

import os
import sys
import argparse
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Settings
OUTPUT_DIR = "/home/ryan/pi_share_receiver/temp/pdf_extract"

def create_annotatable_pdf(content, output_path=None, title="Document"):
    """
    Create a PDF that is optimized for annotation on Remarkable.
    
    Args:
        content (str): Text content to include in the PDF
        output_path (str): Path to save the PDF
        title (str): Document title
    
    Returns:
        str: Path to the created PDF
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, f"annotatable_{int(__import__('time').time())}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create custom style with more spacing for annotations
    styles.add(ParagraphStyle(
        name='SpacedBody',
        parent=styles['Normal'],
        spaceBefore=12,
        spaceAfter=12,
        leading=18
    ))
    
    # Create elements
    elements = []
    
    # Add title
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 24))
    
    # Process content
    paragraphs = content.split('\n\n')
    for paragraph in paragraphs:
        if paragraph.strip():
            if paragraph.startswith('# '):
                # Heading 1
                elements.append(Paragraph(paragraph[2:], styles['Heading1']))
                elements.append(Spacer(1, 12))
            elif paragraph.startswith('## '):
                # Heading 2
                elements.append(Paragraph(paragraph[3:], styles['Heading2']))
                elements.append(Spacer(1, 10))
            elif paragraph.startswith('### '):
                # Heading 3
                elements.append(Paragraph(paragraph[4:], styles['Heading3']))
                elements.append(Spacer(1, 8))
            elif paragraph.strip().startswith('- ') or paragraph.strip().startswith('* '):
                # Bullet list
                lines = paragraph.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('- ') or line.strip().startswith('* '):
                        elements.append(Paragraph(f"• {line.strip()[2:]}", styles['SpacedBody']))
            elif paragraph.strip().startswith('1. ') or paragraph.strip()[0].isdigit() and paragraph.strip()[1:].startswith('. '):
                # Numbered list
                lines = paragraph.strip().split('\n')
                for i, line in enumerate(lines, 1):
                    content = line.strip()
                    if content[0].isdigit() and '. ' in content:
                        content = content[content.index('. ')+2:]
                    elements.append(Paragraph(f"{i}. {content}", styles['SpacedBody']))
            else:
                # Regular paragraph
                elements.append(Paragraph(paragraph, styles['SpacedBody']))
                elements.append(Spacer(1, 18))  # Extra space for annotations
    
    # Build the PDF
    doc.build(elements)
    print(f"Created annotatable PDF: {output_path}")
    
    return output_path

def create_from_url(url, output_path=None):
    """Create an annotatable PDF from a URL."""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        print(f"Fetching content from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Parse content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled"
        
        # Find main content
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', class_='content') or 
            soup.find('div', id='content') or 
            soup.find('div', class_='main') or
            soup.find('div', class_='article') or
            soup.body
        )
        
        # Remove script, style, and nav elements
        if main_content:
            for element in main_content.select('script, style, nav, footer, header'):
                element.extract()
        
        # Extract text
        all_text = main_content.get_text('\n\n', strip=True) if main_content else soup.get_text('\n\n', strip=True)
        
        # Create formatted content
        content = f"# {title}\n\nSource: {url}\n\n{all_text}\n"
        
        # Create PDF
        return create_annotatable_pdf(content, output_path, title)
    except Exception as e:
        print(f"Error creating PDF from URL: {e}")
        return None

def upload_to_remarkable(file_path):
    """Upload file to Remarkable."""
    try:
        import subprocess
        
        cmd = ["/usr/local/bin/rmapi", "put", file_path, "/"]
        print(f"Uploading to Remarkable: {file_path}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error uploading to Remarkable: {result.stderr}")
            return False
        
        print(f"Successfully uploaded {file_path} to Remarkable")
        return True
    except Exception as e:
        print(f"Error uploading to Remarkable: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Create annotatable PDF for Remarkable")
    parser.add_argument("--url", "-u", help="URL to convert to PDF")
    parser.add_argument("--text", "-t", help="Text file to convert")
    parser.add_argument("--output", "-o", help="Output PDF path")
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--upload", action="store_true", help="Upload to Remarkable after creation")
    
    args = parser.parse_args()
    
    if not args.url and not args.text:
        print("Error: Must provide either --url or --text")
        return 1
    
    # Get content
    content = None
    if args.text:
        if not os.path.exists(args.text):
            print(f"Error: Text file not found: {args.text}")
            return 1
            
        with open(args.text, 'r') as f:
            content = f.read()
    
    # Create PDF
    pdf_path = None
    if args.url:
        pdf_path = create_from_url(args.url, args.output)
    elif content:
        title = args.title or "Document"
        pdf_path = create_annotatable_pdf(content, args.output, title)
    
    if not pdf_path:
        print("Failed to create PDF")
        return 1
    
    # Upload if requested
    if args.upload:
        success = upload_to_remarkable(pdf_path)
        if not success:
            print("Failed to upload to Remarkable")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())