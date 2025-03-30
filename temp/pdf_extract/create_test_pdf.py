#!/usr/bin/env python3
"""Create a simple test PDF for conversion."""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

output_path = "/home/ryan/pi_share_receiver/temp/pdf_extract/test_pdf.pdf"

def create_test_pdf():
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # First page
    c.setFont("Helvetica", 24)
    c.drawString(1*inch, 10*inch, "Test PDF for Remarkable")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, 9*inch, "This is a test document to be converted to Remarkable format.")
    c.drawString(1*inch, 8.5*inch, "It should be editable directly on the tablet.")
    
    # Add some lines
    c.line(1*inch, 8*inch, 7*inch, 8*inch)
    c.line(1*inch, 7.5*inch, 7*inch, 7.5*inch)
    c.line(1*inch, 7*inch, 7*inch, 7*inch)
    
    # Add second page
    c.showPage()
    c.setFont("Helvetica", 14)
    c.drawString(1*inch, 10*inch, "Page 2: More Test Content")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, 9*inch, "Testing multiple pages.")
    c.drawString(1*inch, 8.5*inch, "This page should also be editable on Remarkable.")
    
    # Save the PDF
    c.save()
    print(f"Created test PDF: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_pdf()