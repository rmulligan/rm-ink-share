import os
import subprocess
from typing import Optional, Tuple
from .interfaces import IRemarkableService

class RemarkableService(IRemarkableService):
    def __init__(self, rmapi_path: str, upload_folder: str = "/"):
        self.rmapi_path = rmapi_path
        self.upload_folder = upload_folder

    def upload(self, doc_path: str, title: str) -> Tuple[bool, str]:
        """Upload document to Remarkable Cloud"""
        try:
            # Validate inputs
            if not os.path.exists(doc_path):
                return False, f"Document not found: {doc_path}"
            
            if not os.path.exists(self.rmapi_path):
                return False, f"rmapi not found at: {self.rmapi_path}"

            # Run rmapi command
            cmd = [self.rmapi_path, "put", doc_path, self.upload_folder]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                return True, "Upload successful"
            else:
                return False, f"Upload failed: {result.stderr}"
                
        except subprocess.CalledProcessError as e:
            return False, f"rmapi error: {e.stderr}"
        except Exception as e:
            return False, f"Upload error: {str(e)}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for Remarkable"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()