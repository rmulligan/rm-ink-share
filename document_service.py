import os
import time
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, temp_dir: str, drawj2d_path: str):
        """Initialize with directories and paths.
        
        Args:
            temp_dir: Directory for temporary files
            drawj2d_path: Path to drawj2d executable
        """
        self.temp_dir = temp_dir
        self.drawj2d_path = drawj2d_path

    def create_rmdoc(self, hcl_path: str, url: str) -> Optional[str]:
        """Convert HCL to Remarkable document.
        
        Args:
            hcl_path: Path to HCL file
            url: Original URL for naming
                
        Returns:
            Path to created Remarkable document or None if failed
        """
        try:
            # Input validation
            if not os.path.exists(hcl_path):
                logger.error(f"HCL file not found: {hcl_path}")
                return None
                
            if not os.path.exists(self.drawj2d_path):
                logger.error(f"drawj2d executable not found: {self.drawj2d_path}")
                return None
                
            # Check executable permissions
            if not os.access(self.drawj2d_path, os.X_OK):
                logger.error(f"drawj2d exists but is not executable: {self.drawj2d_path}")
                try:
                    logger.info(f"Attempting to fix permissions on drawj2d...")
                    os.chmod(self.drawj2d_path, 0o755)  # rwx r-x r-x
                    logger.info(f"Permission change attempted. New permissions: {oct(os.stat(self.drawj2d_path).st_mode)[-3:]}")
                except Exception as e:
                    logger.error(f"Failed to change permissions: {e}")
                    return None
            
            # Check HCL file size and content validity
            file_size = os.path.getsize(hcl_path)
            if file_size == 0:
                logger.error(f"HCL file is empty: {hcl_path}")
                return None
            logger.info(f"HCL file size: {file_size} bytes")
            
            # Generate output path
            timestamp = int(time.time())
            rm_filename = f"rm_{hash(url)}_{timestamp}.rm"
            rm_path = os.path.join(self.temp_dir, rm_filename)
            
            # Try conversion methods in sequence until one succeeds
            return (self._try_subprocess_conversion(hcl_path, rm_path) or 
                    self._try_basic_conversion(hcl_path, rm_path) or
                    self._try_os_system_conversion(hcl_path, rm_path))
        
        except Exception as e:
            logger.error(f"Error creating Remarkable document: {e}")
            return None
            
    def _try_subprocess_conversion(self, hcl_path: str, rm_path: str) -> Optional[str]:
        """Try conversion using subprocess with recommended flags."""
        try:
            # Run conversion with detailed logging
            cmd = [self.drawj2d_path, "-Trm", "-r229", "-rmv6", "-o", rm_path, hcl_path]
            logger.info(f"METHOD 1: Running drawj2d conversion with subprocess: {' '.join(cmd)}")
            
            # Add more detailed command output capture
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log both stdout and stderr
            if result.stdout:
                logger.info(f"drawj2d stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"drawj2d stderr: {result.stderr}")
            
            # Check output file
            if result.returncode == 0 and os.path.exists(rm_path) and os.path.getsize(rm_path) > 0:
                file_size = os.path.getsize(rm_path)
                logger.info(f"Created RM file: {rm_path} (size: {file_size} bytes)")
                return rm_path
            else:
                logger.error(f"METHOD 1 failed: drawj2d error: Exit code {result.returncode}")
                return None
                
        except Exception as e:
            logger.error(f"METHOD 1 exception: {e}")
            return None
    
    def _try_basic_conversion(self, hcl_path: str, rm_path: str) -> Optional[str]:
        """Try conversion with minimal flags."""
        try:
            # Try with basic options (no Remarkable Pro specific flags)
            cmd = [self.drawj2d_path, "-Trm", "-o", rm_path, hcl_path]
            logger.info(f"METHOD 2: Running basic drawj2d conversion: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                logger.info(f"drawj2d stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"drawj2d stderr: {result.stderr}")
            
            if result.returncode == 0 and os.path.exists(rm_path) and os.path.getsize(rm_path) > 0:
                file_size = os.path.getsize(rm_path)
                logger.info(f"Created RM file with basic options: {rm_path} (size: {file_size} bytes)")
                return rm_path
            else:
                logger.error(f"METHOD 2 failed: Basic conversion error: Exit code {result.returncode}")
                return None
                
        except Exception as e:
            logger.error(f"METHOD 2 exception: {e}")
            return None
    
    def _try_os_system_conversion(self, hcl_path: str, rm_path: str) -> Optional[str]:
        """Try conversion using os.system as fallback."""
        try:
            # Use os.system as final fallback
            cmd_str = f"{self.drawj2d_path} -Trm -r229 -rmv6 -o {rm_path} {hcl_path}"
            logger.info(f"METHOD 3: Running os.system conversion: {cmd_str}")
            
            exit_code = os.system(cmd_str)
            logger.info(f"os.system exit code: {exit_code}")
            
            if exit_code == 0 and os.path.exists(rm_path) and os.path.getsize(rm_path) > 0:
                file_size = os.path.getsize(rm_path)
                logger.info(f"Created RM file with os.system: {rm_path} (size: {file_size} bytes)")
                return rm_path
            else:
                logger.error(f"METHOD 3 failed: os.system conversion error: Exit code {exit_code}")
                return None
                
        except Exception as e:
            logger.error(f"METHOD 3 exception: {e}")
            return None