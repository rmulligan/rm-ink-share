#!/usr/bin/env python3
"""
Debug script for RM document creation
"""

import os
import subprocess
import sys
import time

# Path settings
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"

def debug_create_rm(hcl_path):
    """Debug function for creating RM files"""
    # HCL path must exist
    if not os.path.exists(hcl_path):
        print(f"ERROR: HCL file not found at {hcl_path}")
        return False
        
    # Create output path
    rm_path = f"{os.path.splitext(hcl_path)[0]}_debug.rm"
    
    # Convert HCL to RM format with Lines v6
    print(f"\n===== Testing drawj2d direct command with Lines v6 =====")
    direct_cmd = f"{DRAWJ2D_PATH} -Trm -rmv6 -o {rm_path} {hcl_path}"
    print(f"Running: {direct_cmd}")
    os.system(direct_cmd)
    
    # Check if file was created
    if os.path.exists(rm_path):
        print(f"SUCCESS: RM file created at {rm_path}")
        file_size = os.path.getsize(rm_path)
        print(f"File size: {file_size} bytes")
        
        # Display the first few lines of the RM file
        try:
            with open(rm_path, 'r', errors='ignore') as f:
                content = f.read(100)
                print(f"File content (first 100 chars): {repr(content)}")
        except Exception as e:
            print(f"Error reading RM file: {e}")
            
        return True
    else:
        print(f"ERROR: RM file was not created")
        return False
        
    print("\n===== Testing subprocess.run =====")
    # Try with subprocess
    cmd = [DRAWJ2D_PATH, "-Trm", "-rmv6", "-o", rm_path, hcl_path]
    print(f"Running subprocess: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(rm_path):
            print(f"SUCCESS: RM file created at {rm_path}")
            return True
        else:
            print(f"ERROR: subprocess failed to create RM file")
            return False
            
    except Exception as e:
        print(f"Exception running subprocess: {e}")
        return False
    
def main():
    # Find all HCL files in the temp directory
    hcl_files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.hcl')]
    
    if not hcl_files:
        print("No HCL files found in temp directory")
        return
    
    # Sort by modification time (newest first)
    hcl_files.sort(key=lambda f: os.path.getmtime(os.path.join(TEMP_DIR, f)), reverse=True)
    
    # Use the most recent HCL file
    hcl_path = os.path.join(TEMP_DIR, hcl_files[0])
    print(f"Using most recent HCL file: {hcl_path}")
    
    # Try to convert to RM
    debug_create_rm(hcl_path)
    
if __name__ == "__main__":
    main()