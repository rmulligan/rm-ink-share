#!/usr/bin/env python3
"""
Debug script to test document conversion with drawj2d.
This script attempts to convert a specified HCL file to Remarkable format
using the drawj2d tool, with detailed logging of each step.
"""

import os
import sys
import subprocess
import time

def main():
    """Run the conversion test with detailed logging."""
    if len(sys.argv) < 2:
        print("Usage: python debug_convert.py <hcl_file_path>")
        sys.exit(1)
    
    hcl_path = sys.argv[1]
    drawj2d_path = "/usr/local/bin/drawj2d"
    output_path = "debug_output.rm"
    
    print(f"=== DEBUG CONVERSION TEST ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"HCL file: {hcl_path}")
    print(f"drawj2d path: {drawj2d_path}")
    print(f"Output path: {output_path}")
    
    # Check if HCL file exists
    if not os.path.exists(hcl_path):
        print(f"ERROR: HCL file not found: {hcl_path}")
        sys.exit(1)
    
    # Check if drawj2d exists
    if not os.path.exists(drawj2d_path):
        print(f"ERROR: drawj2d not found: {drawj2d_path}")
        sys.exit(1)
    
    # Print HCL file content
    with open(hcl_path, 'r') as f:
        hcl_content = f.read()
    print(f"\n=== HCL FILE CONTENT ===\n{hcl_content}")
    
    # Check executable permissions
    if not os.access(drawj2d_path, os.X_OK):
        print(f"ERROR: drawj2d exists but is not executable: {drawj2d_path}")
        print(f"Attempting to fix permissions...")
        try:
            os.chmod(drawj2d_path, 0o755)  # rwx r-x r-x
            print(f"Permission change attempted. New permissions: {oct(os.stat(drawj2d_path).st_mode)[-3:]}")
        except Exception as e:
            print(f"Failed to change permissions: {e}")
    
    # Print HCL file stats
    file_size = os.path.getsize(hcl_path)
    print(f"HCL file size: {file_size} bytes")
    
    # Test 1: Basic conversion with subprocess.run
    print("\n=== TEST 1: Basic conversion (subprocess.run) ===")
    cmd = [drawj2d_path, "-Trm", "-o", output_path, hcl_path]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        if os.path.exists(output_path):
            print(f"Output file created: {output_path} ({os.path.getsize(output_path)} bytes)")
        else:
            print(f"Output file NOT created")
    except Exception as e:
        print(f"Exception occurred: {e}")
    
    # Test 2: Remarkable Pro conversion with recommended flags
    print("\n=== TEST 2: Remarkable Pro conversion (subprocess.run) ===")
    rm_pro_path = "debug_output_pro.rm"
    cmd = [drawj2d_path, "-Trm", "-r229", "-rmv6", "-o", rm_pro_path, hcl_path]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        if os.path.exists(rm_pro_path):
            print(f"Output file created: {rm_pro_path} ({os.path.getsize(rm_pro_path)} bytes)")
        else:
            print(f"Output file NOT created")
    except Exception as e:
        print(f"Exception occurred: {e}")
    
    # Test 3: Using os.system approach
    print("\n=== TEST 3: Using os.system ===")
    cmd_str = f"{drawj2d_path} -Trm -r229 -rmv6 -o debug_output_system.rm {hcl_path}"
    print(f"Running command: {cmd_str}")
    
    try:
        exit_code = os.system(cmd_str)
        print(f"Exit code: {exit_code}")
        
        if os.path.exists("debug_output_system.rm"):
            print(f"Output file created: debug_output_system.rm ({os.path.getsize('debug_output_system.rm')} bytes)")
        else:
            print(f"Output file NOT created")
    except Exception as e:
        print(f"Exception occurred: {e}")
        
    # Test 4: Check drawj2d version
    print("\n=== TEST 4: Check drawj2d version ===")
    cmd = [drawj2d_path, "--version"]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    main()
