
#!/usr/bin/env python3
"""
Unit tests for the DocumentService class.
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the service to test
from services.document_service import DocumentService

class TestDocumentService(unittest.TestCase):
    """Tests for the DocumentService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.drawj2d_path = "/usr/local/bin/drawj2d"  # This will be mocked
        self.service = DocumentService(self.temp_dir, self.drawj2d_path)
        
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
        
    def test_init_sets_remarkable_pro_dimensions(self):
        """Test that the service initializes with correct Remarkable Pro dimensions."""
        self.assertEqual(self.service.page_width, 1872)
        self.assertEqual(self.service.page_height, 2404)
        self.assertEqual(self.service.margin, 100)
        
    def test_create_hcl(self):
        """Test creation of HCL file from webpage content."""
        # Create a test QR code file
        qr_path = os.path.join(self.temp_dir, "test_qr.png")
        with open(qr_path, 'w') as f:
            f.write("mock QR code file")
        
        # Mock content
        content = {
            "title": "Test Page",
            "content": "This is a test paragraph.\n\nThis is another paragraph.",
            "structured_content": [
                {"type": "heading", "content": "Test Heading"},
                {"type": "paragraph", "content": "Test paragraph content."}
            ]
        }
        
        # Create HCL file
        hcl_path = self.service.create_hcl("https://example.com", qr_path, content)
        
        # Check that file was created
        self.assertIsNotNone(hcl_path)
        self.assertTrue(os.path.exists(hcl_path))
        
        # Check file contents
        with open(hcl_path, 'r') as f:
            content = f.read()
            self.assertIn("text 100 100", content)  # Check position starts at margin
            self.assertIn("Test Page", content)     # Check title is included
            self.assertIn("https://example.com", content)  # Check URL is included
            
    def test_create_rmdoc_command(self):
        """Test that the drawj2d command is constructed correctly for Remarkable Pro."""
        # Create a test HCL file
        hcl_path = os.path.join(self.temp_dir, "test.hcl")
        with open(hcl_path, 'w') as f:
            f.write("// Test HCL file\n")
            f.write('text 100 100 "Test Title"\n')
        
        # Mock the subprocess.run and os.path.exists to avoid actual command execution
        with patch('subprocess.run') as mock_run:
            # Configure the mock to capture the command but return failure
            # This way we can inspect the command without needing to mock the file creation
            mock_process = MagicMock()
            mock_process.returncode = 1  # Return error so we don't need to mock file existence
            mock_run.return_value = mock_process
            
            # Call the method under test - we expect None since subprocess returns error
            rm_path = self.service.create_rmdoc(hcl_path, "https://example.com")
            
            # We don't care about the return value, but we check that subprocess was called correctly
            self.assertTrue(mock_run.called)
            
            # Get the command arguments and verify they're correct for Remarkable Pro
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], self.drawj2d_path)
            self.assertEqual(args[1], hcl_path)
            self.assertEqual(args[4], "rm")
            
    def test_successful_conversion_and_upload(self):
        """Test successful conversion and upload simulation using mocks."""
        hcl_path = os.path.join(self.temp_dir, "test_success.hcl")
        rm_path = os.path.join(self.temp_dir, "output.rm")
        with open(hcl_path, "w") as f:
            f.write("dummy hcl content")
        successful_result = MagicMock()
        successful_result.returncode = 0
        successful_result.stdout = "Conversion successful"
        successful_result.stderr = ""
        original_exists = os.path.exists
        def fake_exists(path):
            if path == self.drawj2d_path or path == hcl_path or path == rm_path:
                return True
            return original_exists(path)
        with patch('subprocess.run', return_value=successful_result) as mock_run, patch('os.path.exists', side_effect=fake_exists):
            result = self.service.create_rmdoc(hcl_path, rm_path)
            self.assertEqual(result, rm_path)
            self.assertTrue(mock_run.called)
            self.assertEqual(args[4], "rm")  # Check that format is set to rm
            
            # The important part: verify this code is using the document dimensions that are correct
            # Remarkable Pro dimensions were applied in the earlier test_init_sets_remarkable_pro_dimensions test
            # so we don't need to recheck here. This test simply verifies the command execution.

if __name__ == "__main__":
    unittest.main()

