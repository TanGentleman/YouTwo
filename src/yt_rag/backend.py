from typing import List, Optional, Dict, Any, TypedDict
from src.yt_rag.rag import fetch_documents_from_corpus, fetch_document_by_id
import requests
import json
import os
import logging
import time
import argparse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

class VectaraChunkMetadata(TypedDict):
    sidebar_position: str
    title: str

class VectaraChunk(TypedDict):
    metadata: VectaraChunkMetadata
    parts: List[VectaraChunkPart]

class ConvexChunk(TypedDict):
    filename: str
    title: str
    parts: List[Dict[str, Any]]

def convert_to_convex_chunks(documents: list[VectaraChunk]) -> list[ConvexChunk]:
    """
    Converts Vectara chunks to Convex format for database storage.
    
    Args:
        documents: List of VectaraChunk objects
        
    Returns:
        List of ConvexChunk objects formatted for Convex database
    """
    convex_chunks = []
    for doc in documents:
        # Create the base ConvexChunk
        convex_chunk = {
            "filename": doc["id"],
            "title": doc["metadata"].get("title", ""),
            "parts": []
        }
        
        # Convert each part
        for part in doc["parts"]:
            # Initialize metadata with only non-None values
            metadata = {}
            if part["metadata"].get("breadcrumb") is not None:
                metadata["breadcrumb"] = part["metadata"]["breadcrumb"]
            if part["metadata"].get("is_title") is not None:
                metadata["is_title"] = part["metadata"]["is_title"]
            if part["metadata"].get("title") is not None:
                metadata["title"] = part["metadata"]["title"]
            if part["metadata"].get("offset") is not None:
                metadata["offset"] = part["metadata"]["offset"]
            
            convex_part = {
                "text": part["text"],
                "context": part["context"],
                "metadata": metadata
            }
            convex_chunk["parts"].append(convex_part)
        
        convex_chunks.append(convex_chunk)
    
    return convex_chunks

def send_chunks_to_convex(chunks: list[ConvexChunk], start_time: int = None, end_time: int = None) -> Dict[str, Any]:
    """
    Sends the converted chunks to Convex via HTTP POST.
    
    Args:
        chunks: List of ConvexChunk objects to send to Convex
        start_time: Start time in milliseconds since epoch (default: current time)
        end_time: End time in milliseconds since epoch (default: current time)
        
    Returns:
        Dict containing the response status, data, and success flag
        
    Raises:
        Exception: If there's an error sending chunks to Convex
    """
    convex_url = os.getenv("CONVEX_URL")
    if not convex_url:
        raise ValueError("CONVEX_URL environment variable not set")
    
    # Replace .cloud or .cloud/ with .site in the Convex URL
    if "convex.cloud" in convex_url:
        convex_url = convex_url.replace("convex.cloud", "convex.site")
    if not convex_url.endswith("/"):
        convex_url += "/"
        
    endpoint = f"{convex_url}chunks"
    
    # Set default timestamps if not provided
    current_time = int(time.time() * 1000)  # Current time in milliseconds
    if start_time is None:
        start_time = current_time
    if end_time is None:
        end_time = current_time
    
    payload = {
        "chunks": chunks,
        "startTime": start_time,
        "endTime": end_time
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        logger.info(f"Sending request to {endpoint}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload  # Use json parameter instead of data for automatic serialization
        )
        
        try:
            response_data = response.json()
        except:
            response_data = {"message": response.text}
            
        result = {
            "status": response.status_code,
            "data": response_data,
            "ok": response.ok
        }
        
        if not response.ok:
            logger.error(f"Request failed with status {response.status_code}: {response_data}")
        
        return result
    except Exception as e:
        logger.error(f"Error sending chunks to Convex: {str(e)}")
        return {
            "status": 0,
            "error": str(e),
            "ok": False
        }

def main(max_docs: int = 10):
    """
    Main function to process documents and send chunks to Convex.
    
    Args:
        max_docs: Maximum number of documents to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting document processing")
    
    try:
        # 1. Client gets vectara documents 
        success = False
        # Using a hardcoded list for testing
        id_list = ["intro.md"]
        logger.info(f"Processing documents with IDs: {id_list}")
        
        processed_chunks = []
        count = 0
        
        # Track processing time
        start_time = int(time.time() * 1000)
        
        # 2. Client gets vectara document by id for each document
        for doc_id in id_list:
            try:
                logger.info(f"Fetching document with ID: {doc_id}")
                document = fetch_document_by_id(doc_id)
                logger.info(f"Successfully fetched document: {doc_id}")
                
                logger.info(f"Converting document to Convex chunks")
                convex_chunks = convert_to_convex_chunks([document])
                logger.info(f"Generated {len(convex_chunks)} chunks")
                
                processed_chunks.extend(convex_chunks)
                count += 1
                
                if count >= max_docs:
                    logger.info(f"Reached maximum document limit: {max_docs}")
                    break
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {str(e)}")
        
        # Get end time after processing
        end_time = int(time.time() * 1000)
        
        # 3. Send the chunks to Convex if we have any
        if processed_chunks:
            logger.info(f"Sending {len(processed_chunks)} chunks to Convex")
            try:
                result = send_chunks_to_convex(
                    chunks=processed_chunks,
                    start_time=start_time,
                    end_time=end_time
                )
                if result["ok"]:
                    logger.info(f"Successfully sent chunks to Convex: {result['data']}")
                    success = True
                else:
                    logger.error(f"Failed to send chunks to Convex: {result}")
            except Exception as e:
                logger.error(f"Exception sending chunks to Convex: {str(e)}")
        else:
            logger.warning("No chunks to send to Convex")
            
        if success:
            logger.info("All chunks sent successfully to Convex")
        else:
            logger.error("Failed to send all chunks to Convex")
        return success
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
        return False
        
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process documents and send chunks to Convex")
    parser.add_argument("--max-docs", type=int, default=1, help="Maximum number of documents to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-connection", action="store_true", help="Test Convex connection without processing documents")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger.setLevel(log_level)
    
    # Configure console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add the handler to the logger if it doesn't already have it
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(handler)
    
    logger.info(f"Starting with args: {args}")
    
    # Test Convex connection if requested
    if args.test_connection:
        try:
            # Send an empty request to test connection
            logger.info("Testing Convex connection...")
            
            # Create a minimal valid chunk for testing
            test_chunk = {
                "filename": "test.md",
                "title": "Test Document",
                "parts": [{
                    "text": "This is a test chunk",
                    "context": "Test context",
                    "metadata": {
                        "breadcrumb": ["test"],
                        "is_title": True,
                        "title": "Test",
                        "offset": 0
                    }
                }]
            }
            
            result = send_chunks_to_convex([test_chunk])
            if result["ok"]:
                logger.info("Connection to Convex successful!")
                logger.info(f"Response: {result}")
            else:
                logger.error(f"Connection to Convex failed: {result}")
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
        sys.exit(0)
    
    # Run the main function
    try:
        success = main(max_docs=args.max_docs)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}", exc_info=args.debug)
        sys.exit(1)
