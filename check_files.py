#!/usr/bin/env python3
"""
Check for RM files in the temp directory
"""

import os
import sys
import time

TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"

def main():
    # Find all RM and HCL files in the temp directory
    rm_files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.rm')]
    hcl_files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.hcl')]
    
    print(f"Found {len(rm_files)} RM files and {len(hcl_files)} HCL files")
    
    # Sort by modification time (newest first)
    rm_files.sort(key=lambda f: os.path.getmtime(os.path.join(TEMP_DIR, f)), reverse=True)
    hcl_files.sort(key=lambda f: os.path.getmtime(os.path.join(TEMP_DIR, f)), reverse=True)
    
    # Print the most recent files
    if rm_files:
        print("\nMost recent RM files:")
        for f in rm_files[:5]:
            path = os.path.join(TEMP_DIR, f)
            size = os.path.getsize(path)
            mtime = time.ctime(os.path.getmtime(path))
            print(f"{f}: {size} bytes, modified {mtime}")
    
    if hcl_files:
        print("\nMost recent HCL files:")
        for f in hcl_files[:5]:
            path = os.path.join(TEMP_DIR, f)
            size = os.path.getsize(path)
            mtime = time.ctime(os.path.getmtime(path))
            print(f"{f}: {size} bytes, modified {mtime}")
    
    # If there are matching pairs, point them out
    print("\nMatching RM/HCL pairs:")
    found_pairs = 0
    for hcl_file in hcl_files[:10]:
        # Extract the base name without extension
        base_name = os.path.splitext(hcl_file)[0]
        rm_file = base_name + ".rm"
        if rm_file in rm_files:
            hcl_path = os.path.join(TEMP_DIR, hcl_file)
            rm_path = os.path.join(TEMP_DIR, rm_file)
            hcl_size = os.path.getsize(hcl_path)
            rm_size = os.path.getsize(rm_path)
            print(f"PAIR: {base_name}")
            print(f"  HCL: {hcl_size} bytes")
            print(f"  RM: {rm_size} bytes")
            found_pairs += 1
    
    if found_pairs == 0:
        print("No matching pairs found")
            
if __name__ == "__main__":
    main()