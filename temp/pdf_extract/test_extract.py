#!/usr/bin/env python3
"""
Test script for PDF extraction and conversion to Remarkable format.
This demonstrates the workflow for processing a PDF and converting it to 
both text and Remarkable document formats.
"""

import os
import sys
import tempfile
from extract_pdf_text import extract_text_from_pdf, create_remarkable_hcl
from pdf_to_remarkable import create_rm_file, create_rmdoc_package

def create_test_pdf():
    """
    Create a simple test PDF using reportlab.
    Returns the path to the created PDF file.
    """
    import reportlab.pdfgen.canvas
    from reportlab.lib.pagesizes import letter
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
    
    # Create a PDF document
    c = reportlab.pdfgen.canvas.Canvas(pdf_path, pagesize=letter)
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Test PDF Document")
    
    # Add some content
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "This is a test PDF document created for extraction testing.")
    
    # Add a paragraph
    text = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    )
    
    # Split text into lines
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 60:
            lines.append(" ".join(current_line[:-1]))
            current_line = [current_line[-1]]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw the lines
    y = 700
    for line in lines:
        c.drawString(100, y, line)
        y -= 15
    
    # Add a heading
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y, "Sample Heading")
    
    # Add more content
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(100, y, "This is content under the heading.")
    
    # Add a second page
    c.showPage()
    
    # Add content to the second page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "Second Page")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "This demonstrates multi-page extraction.")
    
    # Save the PDF
    c.save()
    
    print(f"Created test PDF at {pdf_path}")
    return pdf_path

def test_extraction_workflow():
    """Test the full PDF extraction and conversion workflow."""
    # Create a test PDF
    pdf_path = create_test_pdf()
    
    # Extract text
    print("\n1. Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Failed to extract text")
        return False
    
    # Save extracted text
    text_path = os.path.join(os.path.dirname(pdf_path), "extracted_text.txt")
    with open(text_path, 'w') as f:
        f.write(text)
    
    print(f"Text extracted and saved to {text_path}")
    print("\nExtracted content sample:")
    print("-" * 40)
    print(text[:300] + "..." if len(text) > 300 else text)
    print("-" * 40)
    
    # Create HCL script
    print("\n2. Creating HCL script...")
    hcl_path = os.path.join(os.path.dirname(pdf_path), "test_output.hcl")
    create_remarkable_hcl(text, output_path=hcl_path, title="Test Document")
    
    # Create RM file
    print("\n3. Converting to RM format...")
    rm_path = os.path.join(os.path.dirname(pdf_path), "test_output.rm")
    
    create_rm_file(hcl_path, output_path=rm_path, resolution=229)
    
    # Create RMDOC package
    print("\n4. Packaging as RMDOC...")
    rmdoc_path = os.path.join(os.path.dirname(pdf_path), "test_output.rmdoc")
    
    create_rmdoc_package(rm_path, output_path=rmdoc_path, title="Test Document")
    
    # Print summary
    print("\nWorkflow complete!")
    print(f"- Original PDF: {pdf_path}")
    print(f"- Extracted text: {text_path}")
    print(f"- HCL script: {hcl_path}")
    print(f"- RM file: {rm_path}")
    print(f"- RMDOC package: {rmdoc_path}")
    
    # Clean up
    print("\nCleanup: Would you like to keep the test files? (y/n)")
    response = input().lower()
    
    if response != 'y':
        for path in [pdf_path, text_path, hcl_path, rm_path, rmdoc_path]:
            if os.path.exists(path):
                os.remove(path)
                print(f"Removed {path}")
    
    return True

if __name__ == "__main__":
    try:
        test_extraction_workflow()
    except Exception as e:
        print(f"Error during testing: {e}")
        sys.exit(1)