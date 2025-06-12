import json
import logging
import os
import time
import argparse
from typing import List, Dict, Any, TypedDict, Optional
import requests

from src.schemas import VectaraDocument, VectaraDocuments
from src.yt_rag.rag import get_vectara_corpus_info, fetch_document_by_id

logger = logging.getLogger(__name__)

# Type definitions
class VectaraChunkPartMetadata(TypedDict, total=False):
    breadcrumb: List[str]
    is_title: bool
    title: str
    offset: int
    lang: str
    len: int
    section: int
    title_level: int

class VectaraChunkPart(TypedDict):
    text: str
    context: str
    custom_dimensions: Dict[str, Any]
    metadata: VectaraChunkPartMetadata

class VectaraChunkMetadata(TypedDict, total=False):
    sidebar_position: str
    title: str

class VectaraChunk(TypedDict):
    metadata: VectaraChunkMetadata
    parts: List[VectaraChunkPart]

class ConvexChunk(TypedDict):
    filename: str
    title: str
    parts: List[Dict[str, Any]]

# API handling functions
def make_convex_api_call(endpoint: str, method: str, data: dict = None) -> Optional[Dict[str, Any]]:
    """Make request to Convex API"""
    FORCE_LOAD_DOTENV = True
    if FORCE_LOAD_DOTENV:
        from dotenv import load_dotenv
        load_dotenv()
    convex_url = os.getenv("CONVEX_URL")
    if not convex_url:
        raise ValueError("CONVEX_URL environment variable not set")
    
    url = f"{convex_url.replace('convex.cloud', 'convex.site').rstrip('/')}/{endpoint}"
    
    try:
        response = requests.request(
            method, url, json=data or {}, 
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        return None

def get_convex_chunk_info() -> Optional[List[Dict[str, Any]]]:
    """Get latest chunk info from Convex"""
    response = make_convex_api_call("chunks/info", "GET")
    if not response or "chunkInfo" not in response:
        logger.warning("No chunk info found in response")
        return None
    return response["chunkInfo"]

def get_chunk_filenames_from_convex() -> List[str]:
    """Get all vectara filenames from Convex"""
    chunk_info = get_convex_chunk_info()
    if not chunk_info:
        logger.warning("No chunk info found in response")
        return []
    return [chunk["filename"] for chunk in chunk_info]

def test_convex_connection() -> bool:
    """Test connection to Convex API"""
    test_chunk = {
        "filename": "test.md",
        "title": "Test Document",
        "parts": [{
            "text": "Test chunk",
            "context": "Test context",
            "metadata": {"breadcrumb": ["test"], "is_title": True, "title": "Test", "offset": 0}
        }]
    }
    
    result = send_chunks_to_convex([test_chunk])
    return result["ok"]

# Data conversion and handling
def convert_to_convex_chunks(documents: List[VectaraChunk]) -> List[ConvexChunk]:
    """Convert Vectara chunks to Convex format"""
    convex_chunks = []
    
    for doc in documents:
        parts = []
        for part in doc["parts"]:
            # Extract only the metadata fields we need
            metadata = {
                k: v for k, v in part["metadata"].items() 
                if v is not None and k in {"breadcrumb", "is_title", "title", "offset"}
            }
            
            parts.append({
                "text": part["text"],
                "context": part["context"],
                "metadata": metadata
            })
            
        convex_chunks.append({
            "filename": doc["id"],
            "title": doc["metadata"].get("title", ""),
            "parts": parts
        })
        
    return convex_chunks

def send_chunks_to_convex(
    chunks: List[ConvexChunk], 
    start_time: int = None, 
    end_time: int = None
) -> Dict[str, Any]:
    """Send chunks to Convex"""
    current_time = int(time.time() * 1000)
    payload = {
        "chunks": chunks,
        "startTime": start_time or current_time,
        "endTime": end_time or current_time
    }
    
    try:
        response = make_convex_api_call("chunks", "POST", payload)
        if not response:
            return {"status": 0, "error": "No response", "ok": False}
        return {"status": 200, "data": response, "ok": True}
    except Exception as e:
        logger.error(f"Send failed: {str(e)}")
        return {"status": 0, "error": str(e), "ok": False}

def save_document_to_file(document: dict, folder_path: str, overwrite: bool = False) -> None:
    """Save a document as JSON file in specified folder"""
    os.makedirs(folder_path, exist_ok=True)
    filename = f"{document['id']}.json"
    filepath = os.path.join(folder_path, filename)
    
    if overwrite or not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(document, f, indent=2)
        logger.debug(f"Saved document {document['id']}")

# Main processing functions
def process_document_batch(doc_ids: List[str], folder_path: str) -> List[ConvexChunk]:
    """Process a batch of document IDs"""
    processed_chunks = []
    
    for doc_id in doc_ids:
        try:
            document = fetch_document_by_id(doc_id)
            if not document:
                logger.error(f"Failed to fetch document {doc_id}")
                continue
                
            save_document_to_file(document, folder_path)
            
            # Skip documents that are too large
            if "storage_usage" in document and document["storage_usage"]["bytes_used"] > 1000000:
                logger.error(f"Document {doc_id} is too large (>1MB)")
                continue
                
            processed_chunks.extend(convert_to_convex_chunks([document]))
            
        except Exception as e:
            logger.error(f"Failed to process {doc_id}: {str(e)}")
            
    return processed_chunks

def sync_vectara_to_convex(max_docs: int = 20, batch_size: int = 1) -> bool:
    """Process documents from Vectara and send to Convex in batches"""
    try:
        # Get existing chunks from Convex
        existing_filenames = get_chunk_filenames_from_convex()
        
        # Fetch document IDs from Vectara
        docs = VectaraDocuments(documents=get_vectara_corpus_info(limit=50)["documents"])
        logger.debug(f"Retrieved {len(docs['documents'])} documents from Vectara")
        
        # Filter out existing documents
        id_list = [doc["id"] for doc in docs["documents"] if doc["id"] not in existing_filenames]
        
        if not id_list:
            logger.info("No new documents to process")
            return True
            
        logger.info(f"Processing {min(max_docs, len(id_list))} of {len(id_list)} new documents")
        
        # Setup document storage
        folder_path = os.path.join(os.path.dirname(__file__), "vectara_documents")
        
        start_time = int(time.time() * 1000)
        all_success = True
        
        # Process documents in batches
        for batch_start in range(0, min(max_docs, len(id_list)), batch_size):
            batch_ids = id_list[batch_start:batch_start + batch_size]
            processed_chunks = process_document_batch(batch_ids, folder_path)
            
            # Send batch if we have any chunks
            if not processed_chunks:
                logger.warning(f"No valid chunks in batch {batch_start}-{batch_start + batch_size}")
                continue
                
            result = send_chunks_to_convex(
                processed_chunks, 
                start_time, 
                int(time.time() * 1000)
            )
            
            if not result["ok"]:
                logger.error(f"Failed to send batch {batch_start}-{batch_start + batch_size}")
                all_success = False
            else:
                logger.info(f"Sent batch with {len(processed_chunks)} chunks")
        
        return all_success
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        return False

def setup_logging(debug: bool = False) -> None:
    """Configure logging based on debug flag"""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main_from_cli() -> bool:
    """Process command line arguments and run the appropriate function"""
    parser = argparse.ArgumentParser(description="Process documents and send chunks to Convex")
    parser.add_argument("--max-docs", type=int, default=1, help="Maximum number of documents to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-connection", action="store_true", help="Test connection to Convex")
    args = parser.parse_args()
    
    setup_logging(args.debug)
    
    if args.test_connection:
        success = test_convex_connection()
        logger.info("Connection successful!" if success else "Connection failed")
        return success
    
    return sync_vectara_to_convex(args.max_docs)

if __name__ == "__main__":
    main_from_cli()
