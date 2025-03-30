import requests
import json
import subprocess
import os

# Get the path to rmapi
RMAPI_PATH = "/usr/local/bin/rmapi"

# First, check if the document was actually uploaded
def list_remarkable_files():
    cmd = [RMAPI_PATH, "ls"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# Check current files on remarkable
print("Current files on Remarkable:")
print(list_remarkable_files())

# Check if the generated rmdoc file exists and is not empty
rmdoc_path = "/home/ryan/pi_share_receiver/temp/rm_-8815170133851030085_1743215364.rmdoc"
if os.path.exists(rmdoc_path):
    file_size = os.path.getsize(rmdoc_path)
    print(f"RMDOC file exists with size: {file_size} bytes")
else:
    print("RMDOC file does not exist")

# Try uploading with a specific document name
title = "2025.03.28 - Notes"
safe_title = "".join([c if c.isalnum() or c in " .-_" else "_" for c in title])
safe_title = safe_title[:50]  # Limit length

print(f"Attempting to upload with title: {safe_title}")
cmd = [RMAPI_PATH, "put", "-n", safe_title, rmdoc_path, "/"]
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Upload result: {result.returncode}")
print(f"Output: {result.stdout}")
if result.stderr:
    print(f"Error: {result.stderr}")

# Check files after upload
print("\nFiles on Remarkable after upload:")
print(list_remarkable_files())