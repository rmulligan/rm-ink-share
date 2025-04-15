#!/usr/bin/env python3
"""
Test script to verify HCL to RM conversion with Remarkable Pro settings.
"""

import os
import sys
import time
import tempfile
import logging
import subprocess
from app.services.document_service import DocumentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('conversion_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Path settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"

def create_test_hcl():
    """Create a test HCL file with various content types."""
    # Create a temporary HCL file
    fd, hcl_path = tempfile.mkstemp(suffix=".hcl", dir=TEMP_DIR)
    os.close(fd)
    
    # Generate test content
    with open(hcl_path, 'w', encoding='utf-8') as f:
        f.write('# Test document for Remarkable Pro\n')
        f.write('puts "size 2160 1620"\n')
        f.write('puts "pen black"\n\n')

        # Title with Lines-Bold font
        f.write('puts "set_font Lines-Bold 36"\n')
        f.write('puts "text 120 120 \\"Test Document for Remarkable Pro\\""\n\n')

        # URL line
        f.write('puts "set_font Lines 20"\n')
        f.write('puts "text 120 170 \\"Source: https://example.com/test\\""\n\n')
        
        # Add a separator line
        f.write('puts "line 120 200 2040 200 width=1.0"\n\n')
        
        # Add paragraph text
        f.write('puts "text 120 250 \\"This is a test document to verify that HCL to Remarkable conversion works correctly for Remarkable Pro tablets.\\""')
        f.write('puts "text 120 290 \\"The document should be properly formatted with Lines font for Remarkable Pro.\\""')
        
        # Draw some shapes
        f.write('puts "circle 1080 600 200"\n')
        f.write('puts "line 400 800 1700 800 width=2"\n')
        f.write('puts "rectangle 400 900 800 200 width=1.5"\n')
        
        # Add a timestamp at the bottom
        f.write('puts "text 120 1500 \\"Generated: ' + time.strftime("%Y-%m-%d %H:%M:%S") + '\\""\n')
    
    logger.info(f"Created test HCL file at {hcl_path}")
    return hcl_path

def test_manual_conversion():
    """Test direct conversion using drawj2d command line."""
    logger.info("Testing manual conversion with drawj2d")
    
    # Create test HCL file
    hcl_path = create_test_hcl()
    rm_path = f"{os.path.splitext(hcl_path)[0]}.rm"
    
    # Direct command with v6 format but WITHOUT -r229 flag
    cmd = f"{DRAWJ2D_PATH} -Trm -rmv6 -o {rm_path} {hcl_path}"
    logger.info(f"Running command: {cmd}")
    
    # Execute command
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Check results
    if result.returncode == 0 and os.path.exists(rm_path):
        file_size = os.path.getsize(rm_path)
        logger.info(f"✅ Manual conversion successful: {rm_path} ({file_size} bytes)")
        
        # Check file content
        try:
            with open(rm_path, 'rb') as f:
                content = f.read(100)
                logger.info(f"File content (first 100 bytes): {content}")
        except Exception as e:
            logger.error(f"Error reading RM file: {e}")
    else:
        logger.error(f"❌ Manual conversion failed")
        logger.error(f"Return code: {result.returncode}")
        logger.error(f"Stdout: {result.stdout}")
        logger.error(f"Stderr: {result.stderr}")
    
    return os.path.exists(rm_path) and os.path.getsize(rm_path) > 50

def test_service_conversion():
    """Test conversion using DocumentService."""
    logger.info("Testing conversion using DocumentService")
    
    # Create document service
    document_service = DocumentService(TEMP_DIR, DRAWJ2D_PATH)
    
    # Create test HCL file
    hcl_path = create_test_hcl()
    
    # Convert using service
    logger.info(f"Converting {hcl_path} using DocumentService")
    rm_path = document_service._convert_to_remarkable(hcl_path, f"{os.path.splitext(hcl_path)[0]}_service.rm")
    
    if rm_path and os.path.exists(rm_path):
        file_size = os.path.getsize(rm_path)
        logger.info(f"✅ Service conversion successful: {rm_path} ({file_size} bytes)")
        return True
    else:
        logger.error(f"❌ Service conversion failed")
        return False

def main():
    """Run conversion tests."""
    print("=== Testing HCL to RM Conversion for Remarkable Pro ===")
    
    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Check if drawj2d is installed
    if not os.path.exists(DRAWJ2D_PATH):
        logger.error(f"❌ drawj2d not found at {DRAWJ2D_PATH}")
        print(f"ERROR: drawj2d not found at {DRAWJ2D_PATH}")
        print("Please install drawj2d and try again.")
        return 1
    
    # Test manual conversion
    manual_result = test_manual_conversion()
    
    # Test service conversion
    service_result = test_service_conversion()
    
    # Print results
    print("\n=== Test Results ===")
    print(f"Manual conversion: {'✅ PASSED' if manual_result else '❌ FAILED'}")
    print(f"Service conversion: {'✅ PASSED' if service_result else '❌ FAILED'}")
    
    if manual_result and service_result:
        print("\n✅ All tests PASSED")
        return 0
    else:
        print("\n❌ Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
