import os
import subprocess
import time
import json

# Configuration
DRAWJ2D_PATH = "/usr/local/bin/drawj2d"  # Path to drawj2d executable
RMAPI_PATH = "/usr/local/bin/rmapi"  # Path to rmapi executable
TEMP_DIR = "/home/ryan/pi_share_receiver/temp/"  # Temp directory
HCL_PATH = "/home/ryan/pi_share_receiver/temp/debug_output.hcl"  # Path to the HCL file

def convert_to_rmdoc(hcl_path):
    """Convert HCL to Remarkable document format using drawj2d."""
    try:
        # Create a unique filename
        timestamp = int(time.time())
        rmdoc_filename = f"debug_output_{timestamp}.rmdoc"
        rmdoc_path = os.path.join(TEMP_DIR, rmdoc_filename)
        
        # Print the HCL file contents for debugging
        print(f"HCL file contents:")
        with open(hcl_path, 'r') as f:
            hcl_content = f.read()
            print(hcl_content)
        
        # Execute drawj2d with verbose mode
        cmd = [DRAWJ2D_PATH, "-v", "-T", "rmdoc", "-o", rmdoc_path, hcl_path]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output and errors
        print(f"Command exit code: {result.returncode}")
        print(f"Command stdout: {result.stdout}")
        print(f"Command stderr: {result.stderr}")
        
        if result.returncode != 0:
            print(f"Error converting to Remarkable format: {result.stderr}")
            return None
        
        # Check if the output file exists
        if os.path.exists(rmdoc_path):
            file_size = os.path.getsize(rmdoc_path)
            print(f"Generated RMDOC file: {rmdoc_path} (size: {file_size} bytes)")
            return rmdoc_path
        else:
            print(f"RMDOC file was not created at {rmdoc_path}")
            return None
        
    except Exception as e:
        print(f"Exception in conversion: {e}")
        return None

def inspect_remarkable_cloud():
    """List files on Remarkable Cloud and check space usage."""
    try:
        # List files
        cmd = [RMAPI_PATH, "ls"]
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Files on Remarkable Cloud:")
        print(result.stdout)
        
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Exception inspecting Remarkable Cloud: {e}")
        return False

def upload_test_document(rmdoc_path):
    """Upload a test document to Remarkable Cloud."""
    try:
        # Upload using a specific name
        test_name = f"Debug_Test_{int(time.time())}"
        
        # Copy the file to have the right name
        new_path = os.path.join(TEMP_DIR, f"{test_name}.rmdoc")
        import shutil
        shutil.copy2(rmdoc_path, new_path)
        print(f"Created copy of file as {new_path}")
        
        # Upload the document
        cmd = [RMAPI_PATH, "put", new_path, "/"]
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Upload exit code: {result.returncode}")
        print(f"Upload stdout: {result.stdout}")
        
        if result.stderr:
            print(f"Upload stderr: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Exception uploading test document: {e}")
        return False

# Main execution
print("Starting debugging process...")
print(f"Converting HCL file: {HCL_PATH}")

rmdoc_path = convert_to_rmdoc(HCL_PATH)

if rmdoc_path:
    print(f"Successfully converted HCL to RMDOC: {rmdoc_path}")
    print("Inspecting Remarkable Cloud...")
    inspect_remarkable_cloud()
    
    print("Uploading test document...")
    if upload_test_document(rmdoc_path):
        print("Test document uploaded successfully")
    else:
        print("Test document upload failed")
else:
    print("Failed to convert HCL to RMDOC")

print("Done")