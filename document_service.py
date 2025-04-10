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
            if not os.path.exists(hcl_path):
                logger.error(f"HCL file not found: {hcl_path}")
                return None
            
            if not os.path.exists(self.drawj2d_path):
                logger.error(f"drawj2d not found at {self.drawj2d_path}")
                return None
            
            # Generate output path
            timestamp = int(time.time())
            rm_filename = f"rm_{hash(url)}_{timestamp}.rm"
            rm_path = os.path.join(self.temp_dir, rm_filename)
            
            # Use drawj2d to convert HCL to reMarkable format
            # The key change is using -Trm -r229 -rmv6 flags for proper editable ink
            cmd = [self.drawj2d_path, "-Trm", "-r229", "-rmv6", "-o", rm_path, hcl_path]
            
            logger.info(f"Running drawj2d conversion: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(rm_path):
                logger.info(f"Created Remarkable document: {rm_path}")
                return rm_path
            else:
                logger.error(f"drawj2d error: {result.stderr}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating Remarkable document: {e}")
            return None