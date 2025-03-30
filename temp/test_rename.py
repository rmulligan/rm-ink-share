import subprocess

doc_name = "rm_-684552422773682697_1743216069"
safe_title = "2025.03.28_Notes"

print(f"Attempting to rename {doc_name} to {safe_title}")
rename_cmd = ["/usr/local/bin/rmapi", "mv", doc_name, safe_title]
print(f"Command: {' '.join(rename_cmd)}")
rename_result = subprocess.run(rename_cmd, capture_output=True, text=True)

print(f"Return code: {rename_result.returncode}")
print(f"Output: {rename_result.stdout}")
if rename_result.stderr:
    print(f"Error: {rename_result.stderr}")

# Check files after rename
print("\nFiles on Remarkable after rename:")
ls_cmd = ["/usr/local/bin/rmapi", "ls"]
ls_result = subprocess.run(ls_cmd, capture_output=True, text=True)
print(ls_result.stdout)