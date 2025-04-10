import os
import subprocess
import logging
import shutil
import uuid
import tempfile
import time
from typing import Optional, Tuple, Any, Callable
from .interfaces import IRemarkableService

# Import config if available, otherwise use defaults
try:
    from config import CONFIG
    MAX_RETRIES = CONFIG.get('MAX_RETRIES', 3)
    RETRY_DELAY = CONFIG.get('RETRY_DELAY', 2)
except ImportError:
    MAX_RETRIES = 3
    RETRY_DELAY = 2

# Set up logger
logger = logging.getLogger(__name__)

class RemarkableService(IRemarkableService):
    def __init__(self, rmapi_path: str, upload_folder: str = "/"):
        self.rmapi_path = rmapi_path
        self.upload_folder = upload_folder
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        
    def _retry_operation(self, operation: Callable[..., Any], *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the operation if successful
        
        Raises:
            Exception: If the operation fails after all retries
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                if retries > 0:
                    logger.info(f"Retry attempt {retries}/{self.max_retries}...")
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Operation failed: {str(e)}. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Operation failed after {self.max_retries} retries: {str(e)}")
                    raise last_error
    def upload(self, doc_path: str, title: str) -> Tuple[bool, str]:
        """Upload document to Remarkable Cloud"""
        try:
            # Validate inputs
            if not os.path.exists(doc_path):
                logger.error(f"Document not found: {doc_path}")
                return False, f"Document not found: {doc_path}"
            
            if not os.path.exists(self.rmapi_path):
                logger.error(f"rmapi not found at: {self.rmapi_path}")
                return False, f"rmapi not found at: {self.rmapi_path}"

            # Use the new upload method with -n flag
            sanitized_title = self._sanitize_filename(title)
            success, message = self._upload_with_n_flag(doc_path, sanitized_title)
            
            if success:
                logger.info(f"Document uploaded successfully: {title}")
                return True, f"Document uploaded to Remarkable: {title}"
            else:
                logger.error(f"Upload failed: {message}")
                return False, message
                
        except Exception as e:
            logger.exception(f"Unexpected error in upload: {str(e)}")
            return False, f"Upload error: {str(e)}"
            
    def upload(self, doc_path: str, title: str) -> Tuple[bool, str]:
        """Upload document to Remarkable Cloud"""
        try:
            # Validate inputs
            if not os.path.exists(doc_path):
                logger.error(f"Document not found: {doc_path}")
                return False, f"Document not found: {doc_path}"
            
            if not os.path.exists(self.rmapi_path):
                logger.error(f"rmapi not found at: {self.rmapi_path}")
                return False, f"rmapi not found at: {self.rmapi_path}"

            # Use the upload method with retries
            sanitized_title = self._sanitize_filename(title)
            try:
                success, message = self._retry_operation(
                    self._upload_with_n_flag,
                    doc_path,
                    sanitized_title
                )
                
                if success:
                    logger.info(f"Document uploaded successfully: {title}")
                    return True, f"Document uploaded to Remarkable: {title}"
                else:
                    logger.error(f"Upload failed: {message}")
                    return False, message
            except Exception as e:
                logger.error(f"Upload failed after retries: {str(e)}")
                return False, f"Upload failed after multiple attempts: {str(e)}"
                
        except Exception as e:
            logger.exception(f"Unexpected error in upload: {str(e)}")
            return False, f"Upload error: {str(e)}"
            
    def _upload_with_n_flag(self, doc_path: str, title: str) -> Tuple[bool, str]:
        """Upload document to Remarkable Cloud with custom title
        
        Args:
            doc_path: Path to the document file
            title: Custom title for the document on Remarkable
            
        Returns:
            Tuple of (success, message)
        """
        # Get file extension to handle the file correctly
        file_ext = os.path.splitext(doc_path)[1].lower()
        safe_path = doc_path
        using_temp_file = False
        
        try:
            # If the path contains spaces or special characters, create a temporary file
            if any(c in doc_path for c in [' ', '(', ')', "'"]):
                temp_dir = tempfile.gettempdir()
                temp_filename = f"upload_{uuid.uuid4().hex[:8]}{file_ext}"
                safe_path = os.path.join(temp_dir, temp_filename)
                
                # Copy the file to the temporary location
                shutil.copy2(doc_path, safe_path)
                using_temp_file = True
                logger.info(f"Created temporary file for upload: {safe_path}")
            
            # Upload with correct filename 
            # The -n flag isn't supported by rmapi, so use simple put command
            cmd = [self.rmapi_path, "put", safe_path, self.upload_folder]
            logger.info(f"Running upload command: {' '.join(cmd)}")
            
            try:
                # First upload the document
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise an exception, we'll handle errors manually
                )
                
                # Log detailed command output for debugging
                logger.info(f"Command exit code: {result.returncode}")
                if result.stdout:
                    logger.info(f"Command stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Command stderr: {result.stderr}")
                
                if result.returncode == 0:
                    # Extract the document ID from the upload output
                    doc_id = None
                    if result.stdout:
                        # Try to extract the ID from output like "document uploaded successfully with ID: abcdef12345"
                        for line in result.stdout.splitlines():
                            if "ID" in line:
                                parts = line.split("ID:")
                                if len(parts) > 1:
                                    doc_id = parts[1].strip()
                                    break
                    
                    # If we found the document ID, try to rename it
                    if doc_id:
                        logger.info(f"Document uploaded with ID: {doc_id}, now renaming to: {title}")
                        # Use rmapi mv command to rename the document
                        mv_cmd = [self.rmapi_path, "mv", doc_id, title]
                        try:
                            mv_result = subprocess.run(
                                mv_cmd,
                                capture_output=True,
                                text=True,
                                check=False
                            )
                            if mv_result.returncode == 0:
                                logger.info(f"Document successfully renamed to: {title}")
                            else:
                                logger.warning(f"Failed to rename document: {mv_result.stderr}")
                        except Exception as rename_error:
                            logger.error(f"Error renaming document: {rename_error}")
                    
                    # Clean up temporary file if we created one
                    if using_temp_file and os.path.exists(safe_path):
                        os.unlink(safe_path)
                        logger.info(f"Removed temporary file: {safe_path}")
                    return True, f"Document uploaded to Remarkable: {title}"
                else:
                    error_msg = result.stderr if result.stderr else f"Command failed with code {result.returncode}"
                    logger.error(f"Upload failed: {error_msg}")
                    
                    # Try fallback method if the command failed
                    logger.info("Attempting fallback upload")
                    
                    # Ensure the file exists before trying fallback
                    if not os.path.exists(safe_path):
                        logger.error(f"File not found for fallback upload: {safe_path}")
                        return False, f"Fallback upload error: File not found"

                    # Use a new file path for the fallback attempt to avoid any issues
                    fallback_path = os.path.join(os.path.dirname(safe_path), f"fallback_{title}_{uuid.uuid4().hex[:8]}{file_ext}")
                    try:
                        # Make a fresh copy for the fallback attempt
                        shutil.copy2(safe_path, fallback_path)
                        logger.info(f"Created copy for fallback attempt: {fallback_path}")
                        
                        simple_cmd = [self.rmapi_path, "put", fallback_path, self.upload_folder]
                        logger.info(f"Running fallback command: {' '.join(simple_cmd)}")
                        
                        fallback_result = subprocess.run(
                            simple_cmd,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        # Log detailed command output for debugging
                        logger.info(f"Fallback command exit code: {fallback_result.returncode}")
                        if fallback_result.stdout:
                            logger.info(f"Fallback command stdout: {fallback_result.stdout}")
                        if fallback_result.stderr:
                            logger.warning(f"Fallback command stderr: {fallback_result.stderr}")
                        
                        # Clean up both temporary files
                        if os.path.exists(fallback_path):
                            os.unlink(fallback_path)
                            logger.info(f"Removed fallback temporary file: {fallback_path}")
                        if using_temp_file and os.path.exists(safe_path):
                            os.unlink(safe_path)
                            logger.info(f"Removed original temporary file: {safe_path}")
                        
                        if fallback_result.returncode == 0:
                            logger.info("Fallback upload succeeded")
                            return True, f"Document uploaded to Remarkable using fallback method: {title}"
                        else:
                            fallback_error = fallback_result.stderr if fallback_result.stderr else f"Fallback command failed with code {fallback_result.returncode}"
                            logger.error(f"Fallback upload also failed: {fallback_error}")
                            return False, f"Upload error: Both primary and fallback methods failed"
                    
                    except Exception as fallback_error:
                        logger.error(f"Error in fallback upload: {fallback_error}")
                        # Clean up any remaining temporary files
                        if os.path.exists(fallback_path):
                            os.unlink(fallback_path)
                        if using_temp_file and os.path.exists(safe_path):
                            os.unlink(safe_path)
                        return False, f"Upload error: Fallback method failed - {str(fallback_error)}"
                    
            except subprocess.SubprocessError as se:
                logger.error(f"Subprocess error: {str(se)}")
                # Don't delete the file yet as we might need it for the fallback approach
                return False, f"Subprocess error: {str(se)}"
                
        except Exception as e:
            logger.exception(f"Exception in n-flag upload method: {e}")
            # Clean up temporary file if we created one and an exception occurred
            if using_temp_file and os.path.exists(safe_path):
                os.unlink(safe_path)
                logger.info(f"Removed temporary file after exception: {safe_path}")
            return False, f"Upload preparation error: {str(e)}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for Remarkable"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()