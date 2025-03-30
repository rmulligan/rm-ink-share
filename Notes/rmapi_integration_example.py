#!/home/ryan/remarkable_ai/venv/bin/python
"""
rmapi_integration_example.py

This example script demonstrates how to use the rmapi integration with the
memory_system and index_generation modules to create a workflow for processing
reMarkable documents, storing information in the memory system, and generating
index pages.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime

# Add project directory to path to ensure imports work
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rmapi_integration_example")

# Import the rmapi integration components
from integrations.rmapi.client import RmapiClient
from integrations.rmapi.handler import RmapiHandler, process_all_tagged_documents
from integrations.rmapi.document_processor import (
    DocumentProcessor,
    extract_text_from_file,
    extract_annotations_from_file
)

# Import memory system components
from helpers.memory_system.memory_system import (
    MemorySystem,
    store_document,
    retrieve_document,
    search_by_tags,
    get_related_documents
)

# Import index generation components
from helpers.index_generation.index_generator import (
    generate_index_page,
    update_index_with_document
)


def setup_rmapi_connection() -> RmapiHandler:
    """
    Set up connection to the reMarkable Cloud.
    
    Returns:
        RmapiHandler: Configured handler for interacting with reMarkable Cloud
    """
    logger.info("Setting up connection to reMarkable Cloud...")
    
    # Create a new handler with auto_connect=True to automatically authenticate
    handler = RmapiHandler(auto_connect=True)
    
    if handler.connected:
        logger.info("Successfully connected to reMarkable Cloud")
    else:
        logger.error("Failed to connect to reMarkable Cloud")
        raise ConnectionError("Could not connect to reMarkable Cloud")
    
    return handler


def download_and_process_tagged_documents(
    handler: RmapiHandler,
    tags: List[str] = ["process", "memory", "index"],
    output_dir: str = "/tmp/remarkable_docs"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Download and process documents with specific tags from reMarkable Cloud.
    
    Args:
        handler: RmapiHandler instance for reMarkable Cloud interactions
        tags: List of tags to look for
        output_dir: Directory to save downloaded documents
        
    Returns:
        Dict mapping document IDs to their processed content
    """
    logger.info(f"Looking for documents with tags: {tags}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Dictionary to store processed documents
    processed_documents = {}
    
    # Process each tag and collect documents
    for tag in tags:
        logger.info(f"Processing documents with tag: {tag}")
        
        # Get documents with this tag
        tagged_docs = handler.get_tagged_documents(tag)
        logger.info(f"Found {len(tagged_docs)} documents with tag '{tag}'")
        
        for doc in tagged_docs:
            doc_id = doc.get("id")
            doc_name = doc.get("name", f"unknown-{doc_id}")
            
            if not doc_id:
                logger.warning(f"Document {doc_name} has no ID, skipping")
                continue
            
            safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in doc_name)
            output_path = os.path.join(output_dir, f"{safe_name}.pdf")
            
            logger.info(f"Downloading document '{doc_name}' to {output_path}")
            success = handler.download_file(doc_id, output_path, include_annotations=True)
            
            if success:
                logger.info(f"Successfully downloaded {doc_name}")
                
                # Process the document to extract text and annotations
                text_content = extract_text_from_file(output_path)
                
                # Get annotations file (created by the handler during download)
                annotations_file = Path(output_path).with_suffix('.annotations.json')
                annotations = []
                
                if annotations_file.exists():
                    # In a real implementation, you would parse the annotations file
                    logger.info(f"Found annotations file: {annotations_file}")
                
                # Store processed document
                if doc_id not in processed_documents:
                    processed_documents[doc_id] = {
                        "id": doc_id,
                        "name": doc_name,
                        "file_path": output_path,
                        "text_content": text_content,
                        "tags": doc.get("tags", []),
                        "annotations": annotations,
                        "metadata": doc
                    }
            else:
                logger.error(f"Failed to download document {doc_name}")
    
    return processed_documents


def store_documents_in_memory_system(
    processed_documents: Dict[str, Dict[str, Any]],
    memory_system: Optional[MemorySystem] = None
) -> Dict[str, str]:
    """
    Store processed documents in the memory system.
    
    Args:
        processed_documents: Dictionary of processed document information
        memory_system: Optional MemorySystem instance (creates a new one if None)
        
    Returns:
        Dict mapping document IDs to memory IDs
    """
    logger.info(f"Storing {len(processed_documents)} documents in memory system")
    
    # Create memory system if not provided
    if memory_system is None:
        memory_system = MemorySystem()
    
    memory_ids = {}
    
    for doc_id, doc_info in processed_documents.items():
        doc_name = doc_info.get("name", f"unknown-{doc_id}")
        text_content = doc_info.get("text_content", "")
        
        if not text_content:
            logger.warning(f"No text content for document {doc_name}, skipping")
            continue
        
        logger.info(f"Adding document '{doc_name}' to memory system")
        
        # Extract some basic entities from the document metadata
        entities = []
        for tag in doc_info.get("tags", []):
            entities.append({
                "name": tag,
                "type": "tag",
                "relevance": 1.0,
                "context": f"Document tagged with '{tag}'"
            })
        
        # Add document creation date as an entity if available
        if "created_at" in doc_info.get("metadata", {}):
            created_at = doc_info["metadata"]["created_at"]
            entities.append({
                "name": created_at,
                "type": "date",
                "relevance": 1.0,
                "context": f"Document created at {created_at}"
            })
        
        # Store the document in memory
        try:
            memory_id = store_document(
                content=text_content,
                source="remarkable_document",
                metadata={
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "tags": doc_info.get("tags", []),
                    "created_at": doc_info.get("metadata", {}).get("created_at", str(datetime.datetime.now())),
                    "entities": entities
                }
            )
            
            memory_ids[doc_id] = memory_id
            logger.info(f"Document '{doc_name}' stored in memory with ID: {memory_id}")
            
            # Add to knowledge graph - connecting document to its entities
            for entity in entities:
                memory_system.add_to_knowledge_graph(
                    entity["name"],
                    "appears_in",
                    doc_name,
                    context=entity.get("context", "")
                )
        
        except Exception as e:
            logger.error(f"Failed to store document '{doc_name}' in memory: {str(e)}")
    
    return memory_ids


def generate_index_pages(
    processed_documents: Dict[str, Dict[str, Any]],
    memory_ids: Dict[str, str],
    output_dir: str = "/tmp/remarkable_indexes"
) -> List[str]:
    """
    Generate index pages for processed documents.
    
    Args:
        processed_documents: Dictionary of processed document information
        memory_ids: Mapping of document IDs to memory IDs
        output_dir: Directory to save generated index pages
        
    Returns:
        List of paths to generated index files
    """
    logger.info("Generating index pages for processed documents")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Group documents by tags
    tag_to_docs = {}
    for doc_id, doc_info in processed_documents.items():
        for tag in doc_info.get("tags", []):
            if tag not in tag_to_docs:
                tag_to_docs[tag] = []
            tag_to_docs[tag].append({
                "id": doc_id,
                "name": doc_info.get("name", f"unknown-{doc_id}"),
                "memory_id": memory_ids.get(doc_id, ""),
                "tags": doc_info.get("tags", []),
                "created_at": doc_info.get("metadata", {}).get("created_at", "")
            })
    
    # Generate index pages for each tag
    generated_files = []
    for tag, docs in tag_to_docs.items():
        if not docs:
            continue
            
        index_file = os.path.join(output_dir, f"{tag}_index.md")
        rm_index_file = os.path.join(output_dir, f"{tag}_index.rm")
        
        logger.info(f"Generating index for tag '{tag}' with {len(docs)} documents")
        
        # Generate the index page
        try:
            # In a real implementation, this would call the actual index generator
            # For this example, we'll create a simple markdown file
            with open(index_file, "w") as f:
                f.write(f"# Document Index: {tag}\n\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for doc in sorted(docs, key=lambda x: x.get("created_at", ""), reverse=True):
                    f.write(f"## {doc['name']}\n\n")
                    f.write(f"- Document ID: {doc['id']}\n")
                    f.write(f"- Memory ID: {doc['memory_id']}\n")
                    f.write(f"- Tags: {', '.join(doc['tags'])}\n")
                    if doc.get("created_at"):
                        f.write(f"- Created: {doc['created_at']}\n")
                    f.write("\n")
            
            logger.info(f"Successfully generated index file: {index_file}")
            generated_files.append(index_file)
            
            # Convert to reMarkable format (simplified for example)
            # In a real implementation, you would use your index_generation module here
            with open(rm_index_file, "w") as f:
                f.write(f"# This would be the reMarkable format of the {tag} index")
            
            logger.info(f"Created reMarkable index file: {rm_index_file}")
            generated_files.append(rm_index_file)
            
        except Exception as e:
            logger.error(f"Failed to generate index for tag '{tag}': {str(e)}")
    
    return generated_files


def upload_index_to_remarkable(
    handler: RmapiHandler,
    index_files: List[str],
    destination: str = "/Indexes"
) -> bool:
    """
    Upload generated index pages back to reMarkable.
    
    Args:
        handler: RmapiHandler instance for reMarkable Cloud interactions
        index_files: List of paths to index files to upload
        destination: Destination folder on reMarkable
        
    Returns:
        True if all uploads were successful, False otherwise
    """
    logger.info(f"Uploading {len(index_files)} index files to reMarkable")
    
    all_success = True
    
    for index_file in index_files:
        if not index_file.endswith(".rm"):
            logger.info(f"Skipping non-reMarkable file: {index_file}")
            continue
            
        file_name = os.path.basename(index_file)
        logger.info(f"Uploading {file_name} to {destination}")
        
        success = handler.upload_file(
            file_path=index_file,
            destination=destination,
            tags=["index", "auto-generated"]
        )
        
        if success:
            logger.info(f"Successfully uploaded {file_name}")
        else:
            logger.error(f"Failed to upload {file_name}")
            all_success = False
    
    return all_success


def run_complete_workflow(
    output_dir: str = "/tmp/remarkable_workflow",
    tags_to_process: List[str] = ["process", "memory", "index"]
) -> None:
    """
    Run a complete workflow that demonstrates the integration between
    rmapi, memory_system, and index_generation modules.
    
    Args:
        output_dir: Base directory for workflow outputs
        tags_to_process: List of tags to look for in reMarkable documents
    """
    logger.info("Starting reMarkable integration workflow")
    
    # Create base output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup directories for different stages
    docs_dir = os.path.join(output_dir, "documents")
    indexes_dir = os.path.join(output_dir, "indexes")
    
    try:
        # Step 1: Connect to reMarkable Cloud
        handler = setup_rmapi_connection()
        
        # Step 2: Download and process tagged documents
        processed_docs = download_and_process_tagged_documents(
            handler=handler,
            tags=tags_to_process,
            output_dir=docs_dir
        )
        
        if not processed_docs:
            logger.warning("No documents were processed. Workflow complete.")
            return
            
        logger.info(f"Successfully processed {len(processed_docs)} documents")
        
        # Step 3: Create memory system and store documents
        memory_system = MemorySystem()
        memory_ids = store_documents_in_memory_system(
            processed_documents=processed_docs,
            memory_system=memory_system
        )
        
        logger.info(f"Added {len(memory_ids)} documents to memory system")
        
        # Step 4: Generate index pages
        index_files = generate_index_pages(
            processed_documents=processed_docs,
            memory_ids=memory_ids,
            output_dir=indexes_dir
        )
        
        if not index_files:
            logger.warning("No index files were generated.")
        else:
            logger.info(f"Generated {len(index_files)} index files")
            
            # Step 5: Upload index pages to reMarkable
            upload_success = upload_index_to_remarkable(
                handler=handler,
                index_files=index_files
            )
            
            if upload_success:
                logger.info("Successfully uploaded all index files to reMarkable")
            else:
                logger.warning("Some index files failed to upload")
        
        # Optional: Remove documents with 'archive' tag from reMarkable
        archive_tag = "archive"
        if archive_tag in tags_to_process:
            archive_docs = handler.get_tagged_documents(archive_tag)
            
            if archive_docs:
                logger.info(f"Found {len(archive_docs)} documents to archive")
                for doc in archive_docs:
                    doc_id = doc.get("id")
                    if doc_id:
                        success = handler.archive_document(doc_id)
                        if success:
                            logger.info(f"Successfully archived document {doc.get('name', doc_id)}")
                        else:
                            logger.error(f"Failed to archive document {doc.get('name', doc_id)}")
        
        logger.info("reMarkable integration workflow completed successfully")
    
    except ConnectionError as e:
        logger.error(f"Connection error during workflow: {str(e)}")
    except Exception as e:
        logger.error(f"Error during workflow: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="reMarkable API Integration Example")
    parser.add_argument("--output-dir", default="/tmp/remarkable_workflow", 
                        help="Base directory for workflow outputs")
    parser.add_argument("--tags", default="process,memory,index", 
                        help="Comma-separated list of tags to process")
    parser.add_argument("--verbose", action="store_true", 
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Split the tags string into a list
    tags_list = [tag.strip() for tag in args.tags.split(",")]
    
    logger.info(f"Starting example with tags: {tags_list}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Run the complete workflow
    run_complete_workflow(
        output_dir=args.output_dir,
        tags_to_process=tags_list
    )
