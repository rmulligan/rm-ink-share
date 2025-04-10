#!/usr/bin/env python3
import unittest
import os
import tempfile
import shutil
from document_service import DocumentService

class TestDocumentService(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_drawj2d_path = "/path/to/mock/drawj2d"  # This will be mocked
        self.service = DocumentService(self.test_drawj2d_path, self.temp_dir)
        
        # Create a mock HCL file for testing
        self.test_hcl_path = os.path.join(self.temp_dir, "test.hcl")
        with open(self.test_hcl_path, 'w') as f:
            f.write("Test HCL content")
            
    def tearDown(self):
        # Clean up temporary files and directories
        shutil.rmtree(self.temp_dir)

    def test_create_rmdoc_missing_hcl(self):
        # Test with a non-existent HCL file
        result = self.service.create_rmdoc("/non/existent/path.hcl", "http://example.com")
        self.assertIsNone(result)
        
    def test_create_rmdoc_missing_drawj2d(self):
        # Test with missing drawj2d executable
        service_with_missing_drawj2d = DocumentService("/non/existent/drawj2d", self.temp_dir)
        result = service_with_missing_drawj2d.create_rmdoc(self.test_hcl_path, "http://example.com")
        self.assertIsNone(result)
        
    def test_create_rmdoc_with_mock(self):
        import unittest.mock as mock
        
        # Create a mock for subprocess.run
        with mock.patch('subprocess.run') as mock_run:
            # Configure the mock to return a successful result
            mock_process = mock.Mock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            mock_run.return_value = mock_process
            
            # Mock os.path.exists to return True for the drawj2d path and the result file
            with mock.patch('os.path.exists') as mock_exists:
                def side_effect(path):
                    # Return True for the input file, drawj2d path, and the output file
                    return True
                mock_exists.side_effect = side_effect
                
                # Test the create_rmdoc method
                url = "http://example.com"
                result = self.service.create_rmdoc(self.test_hcl_path, url)
                
                # Verify the result is not None
                self.assertIsNotNone(result)
                
                # Check if subprocess.run was called with the correct arguments
                expected_cmd = [self.test_drawj2d_path, "-Trm", "-r229", "-rmv6", 
                               "-o", mock.ANY, self.test_hcl_path]
                mock_run.assert_called_once()
                cmd_args = mock_run.call_args[0][0][:6] + [mock_run.call_args[0][0][6]]
                self.assertEqual(cmd_args, expected_cmd)
                
    def test_create_rmdoc_conversion_failure(self):
        import unittest.mock as mock
        
        # Create a mock for subprocess.run
        with mock.patch('subprocess.run') as mock_run:
            # Configure the mock to return a failed result
            mock_process = mock.Mock()
            mock_process.returncode = 1
            mock_process.stderr = "Mock conversion error"
            mock_run.return_value = mock_process
            
            # Test the create_rmdoc method
            result = self.service.create_rmdoc(self.test_hcl_path, "http://example.com")
            
            # Verify the result is None due to conversion failure
            self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()