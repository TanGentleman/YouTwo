import argparse
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from youtwo.rag.vectara_client import VectaraClient
from youtwo.schemas import ConvexSource, VectaraDoc
from youtwo.utils import save_dict_to_file

logger = logging.getLogger(__name__)


# API handling functions
def make_convex_api_call(
    endpoint: str, method: str, data: dict = None, url: str | None = None
) -> Optional[Dict[str, Any]]:
    """Make request to Convex API"""
    if url is None:
        from dotenv import load_dotenv

        load_dotenv()
        convex_url = os.getenv("CONVEX_URL")
        if not convex_url:
            raise ValueError("CONVEX_URL environment variable not set")
    else:
        convex_url = url
    convex_url = f"{convex_url.replace('convex.cloud', 'convex.site')}"
    try:
        print("convex_url: ", convex_url)
        assert convex_url.endswith(".site"), "Convex HTTP api base must end with .site"
        url = f"{convex_url}/{endpoint}"
        response = requests.request(
            method, url, json=data or {}, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        return None


def get_source_filenames_from_convex() -> List[str]:
    """Get filenames from source list in Convex metadata table."""
    response = make_convex_api_call("metadata", "GET")
    if not response or "sourceInfo" not in response:
        logger.warning("No source info found in Convex metadata.")
        return []
    return [source["filename"] for source in response["sourceInfo"]]


def test_convex_connection() -> bool:
    """Test connection to Convex API"""
    test_source = {
        "filename": "test.md",
        "title": "Test Document",
        "partsCount": 1,
        "type": "Test",
    }

    result = upload_sources_to_convex([test_source])
    return result["ok"]


# Data conversion and handling
def convert_to_convex_sources(documents: List[VectaraDoc]) -> List[ConvexSource]:
    """
    Convert Vectara documents to Convex sources format
    """
    convex_sources = []
    for doc in documents:
        title = doc.get("metadata", {}).get("title", "")
        partsCount = len(doc["parts"])
        convex_sources.append(
            {
                "filename": doc["id"],
                "title": title,
                "type": "Vectara",
                "partsCount": partsCount,
            }
        )
    return convex_sources


def upload_sources_to_convex(
    sources: List[ConvexSource],
) -> Dict[str, Any]:
    """Send sources to Convex"""
    payload = {
        "sources": sources,
    }
    try:
        response = make_convex_api_call("sources", "POST", payload)
        if not response:
            return {"status": 0, "error": "No response", "ok": False}
        return {"status": 200, "data": response, "ok": True}
    except Exception as e:
        logger.error(f"Send failed: {str(e)}")
        return {"status": 0, "error": str(e), "ok": False}


# Main processing functions
def process_document_batch(doc_ids: List[str], folder_path: str) -> List[ConvexSource]:
    """Process a batch of document IDs"""
    processed_sources = []

    for doc_id in doc_ids:
        try:
            client = VectaraClient()
            document = client.fetch_document_by_id(doc_id)
            if not document:
                logger.error(f"Failed to fetch document {doc_id}")
                continue

            filepath = os.path.join(folder_path, f"{doc_id}.json")
            save_dict_to_file(document, filepath)

            # Skip documents that are too large
            if (
                "storage_usage" in document
                and document["storage_usage"]["bytes_used"] > 1000000
            ):
                logger.error(f"Document {doc_id} is too large (>1MB)")
                continue

            processed_sources.extend(convert_to_convex_sources([document]))

        except Exception as e:
            logger.error(f"Failed to process {doc_id}: {str(e)}")

    return processed_sources

def setup_logging(debug: bool = False) -> None:
    """Configure logging based on debug flag"""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main_from_cli() -> bool:
    """Process command line arguments and run the appropriate function"""
    from youtwo.rag.pipelines import sync_vectara_to_convex
    parser = argparse.ArgumentParser(
        description="Process documents and send chunks to Convex"
    )
    parser.add_argument(
        "--max-docs", type=int, default=1, help="Maximum number of documents to process"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--test-connection", action="store_true", help="Test connection to Convex"
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    if args.test_connection:
        success = test_convex_connection()
        logger.info("Connection successful!" if success else "Connection failed")
        return success

    return sync_vectara_to_convex(args.max_docs)


if __name__ == "__main__":
    main_from_cli()
