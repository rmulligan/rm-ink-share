#!/usr/bin/env python3
import os
import uuid
import json
import shutil
import tarfile
import tempfile
import subprocess
from datetime import datetime

# Constants
RM_HEADER = b'reMarkable .lines file, version=5           \x01\x00\x00\x00\x00\x00\x00'

def create_remarkable_document(name):
    """Create a ReMarkable document"""
    temp_dir = tempfile.mkdtemp()
    
    # Create document structure
    doc_uuid = str(uuid.uuid4())
    page_uuid = str(uuid.uuid4())
    doc_dir = os.path.join(temp_dir, doc_uuid)
    os.makedirs(doc_dir)
    
    # Create page file (empty RM file with header only)
    page_file = os.path.join(doc_dir, f"{page_uuid}.rm")
    with open(page_file, 'wb') as f:
        f.write(RM_HEADER)
    
    # Create page metadata
    meta_file = os.path.join(doc_dir, f"{page_uuid}-metadata.json")
    with open(meta_file, 'w') as f:
        json.dump({"layers": [{"name": "Layer 1"}]}, f)
    
    # Create document metadata
    timestamp = int(datetime.now().timestamp() * 1000)
    metadata = {
        "deleted": False,
        "lastModified": str(timestamp),
        "lastOpened": str(timestamp),
        "lastOpenedPage": 0,
        "metadatamodified": False,
        "modified": True,
        "parent": "",
        "pinned": False,
        "synced": False,
        "type": "DocumentType",
        "version": 0,
        "visibleName": name
    }
    
    with open(os.path.join(temp_dir, f"{doc_uuid}.metadata"), 'w') as f:
        json.dump(metadata, f)
    
    # Create content file
    content = {
        "extraMetadata": {},
        "fileType": "notebook",
        "lineHeight": -1,
        "margins": 125,
        "orientation": "portrait",
        "pageCount": 1,
        "textAlignment": "left",
        "textScale": 1
    }
    
    with open(os.path.join(temp_dir, f"{doc_uuid}.content"), 'w') as f:
        json.dump(content, f)
    
    # Create pagedata (just "Blank" for this example)
    with open(os.path.join(temp_dir, f"{doc_uuid}.pagedata"), 'w') as f:
        f.write("Blank")
    
    # Create tar archive
    output_file = os.path.join(os.path.dirname(temp_dir), f"{name}.zip")
    
    # Create zip archive (ReMarkable expects a zip file with .rmdoc extension)
    shutil.make_archive(os.path.splitext(output_file)[0], 'zip', temp_dir)
    
    # Upload using rmapi
    rmdoc_path = os.path.splitext(output_file)[0] + ".zip"
    final_path = os.path.splitext(output_file)[0] + ".rmdoc"
    os.rename(rmdoc_path, final_path)
    
    print(f"Created file: {final_path}")
    
    rmapi_cmd = ["/usr/local/bin/rmapi", "put", final_path, "/"]
    subprocess.run(rmapi_cmd)
    
    return final_path

# Create test document
create_remarkable_document("Direct_Test_Document")