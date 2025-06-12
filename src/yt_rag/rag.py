import json
import logging
import os
from pathlib import Path
import requests
from pprint import pprint
from src.schemas import UploadResult

CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key

logger = logging.getLogger(__name__)

class VectaraAPIError(Exception):
    """Custom exception for Vectara API errors."""
    pass

class IndexingError(Exception):
    """Custom exception for general Indexing errors."""
    pass

def load_environment_variables():
    """
    Load environment variables from a .env file.
    This function is useful for local development to avoid hardcoding sensitive information.
    """
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("VECTARA_API_KEY"):
        raise IndexingError("Vectara API key not set. Please set the VECTARA_API_KEY environment variable.")


class MetadataFilter:
    """
    A helper class to build metadata filter strings for Vectara queries.
    (Placeholder implementation)
    
    Example:
        filter_str = MetadataFilter().by_doc_id("my-doc-id").build()
    """
    def __init__(self):
        self.filters = []

    def by_doc_id(self, doc_id: str):
        """Adds a filter for a specific document ID."""
        self.filters.append(f"doc.id = '{doc_id}'")
        return self
    
    def by_metadata_field(self, field: str, value: str):
        """Adds a filter for a specific metadata field."""
        self.filters.append(f"metadata.{field} = '{value}'")
        return self

    def build(self, operator: str = " and ") -> str:
        """
        Returns the constructed filter string.
        
        Args:
            operator (str): The operator to join multiple filters (e.g., " and ", " or ").
        """
        return operator.join(self.filters)

    def __str__(self):
        return self.build()

def make_vectara_api_call(method: str, endpoint: str, **kwargs) -> dict:
    """
    Makes a request to the Vectara API.

    Args:
        method (str): The HTTP method (e.g., 'GET', 'POST').
        endpoint (str): The API endpoint (e.g., 'corpora/123/query').
        **kwargs: Additional arguments to pass to requests.request() like 'json', 'params', 'files'.

    Returns:
        dict: The JSON response from the API.

    Raises:
        VectaraAPIError: If the API call fails.
    """
    base_url = "https://api.vectara.io/v2"
    url = f"{base_url}/{endpoint}"

    api_key = os.getenv("VECTARA_API_KEY")
    if not api_key:
        raise VectaraAPIError("Vectara API key not set. Please set the VECTARA_API_KEY environment variable.")

    headers = kwargs.pop("headers", {})
    headers.update({
        "Accept": "application/json",
        "x-api-key": api_key,
    })
    
    if 'json' in kwargs:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()
    except requests.exceptions.RequestException as e:
        raise VectaraAPIError(f"Error calling Vectara API endpoint {endpoint}: {e}") from e
    except json.JSONDecodeError:
        raise VectaraAPIError(f"Error decoding JSON response from Vectara API endpoint {endpoint}: {response.text}")
    except Exception as e:
        raise VectaraAPIError(f"An unexpected error occurred during Vectara API call: {e}") from e


def is_allowed_filetype(suffix: str):
    # Commonmark / Markdown (md extension).
    # PDF/A (pdf).
    # Open Office (odt).
    # Microsoft Word (doc, docx).
    # Microsoft Powerpoint (ppt, pptx).
    # Text files (txt).
    # HTML files (.html).
    # LXML files (.lxml).
    # RTF files (.rtf).
    # ePUB files (.epub).
    return suffix in [".md", ".pdf", ".odt", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".html", ".lxml", ".rtf", ".epub"]

def save_response_to_file(response_json: dict, filename: str):
    """
    Saves the Vectara API response to a JSON file.

    Args:
        response_json (dict): The Vectara API response.
        filename (str): The name of the file to save the response to.
    """
    with open(filename, "w") as f:
        json.dump(response_json, f, indent=2)

def upload_file_to_vectara(file_bytes: bytes, filename: str)  -> UploadResult:
    """
    Uploads a supported file type to Vectara for processing.

    Args:
        file_bytes (bytes): The file content in bytes.
        filename (str): The name of the file.

    Returns:
        UploadResult: The upload result containing information about the uploaded file.

    Raises:
        VectaraAPIError: If there's an error during the Vectara API call.
        IndexingError: For other processing errors.
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key

    # Check if file_bytes is provided
    if not file_bytes:
        raise IndexingError("No file bytes provided.")
    
    suffix = Path(filename).suffix
    # Ensure valid filename
    if not is_allowed_filetype(suffix):
        raise IndexingError(f"Invalid file type: {suffix}. Please provide a supported file type.")

    endpoint = f"corpora/{CORPUS_KEY}/upload_file"
    files = {'file': (filename, file_bytes)}

    try:
        response_json = make_vectara_api_call("POST", endpoint, files=files)
        result = process_upload_response(response_json)
        # You might want to store some information from the Vectara response
        # in your session object, e.g., document ID.
        return result
    except VectaraAPIError as e:
        raise VectaraAPIError(f"Error uploading file '{filename}' to Vectara: {e}") from e


def process_upload_response(response_json: dict) -> UploadResult:
    """
    Processes the Vectara API response after a file upload.

    Args:
        response_json (dict): The Vectara API response.

    Returns:
        UploadResult: The upload result.
    """
    log_filename = "upload_results.json"
    save_response_to_file(response_json, log_filename)
    logger.info(f"Saved response to file: {log_filename}")
    # pprint(response_json)

    return UploadResult(
        id=response_json["id"],
        metadata=response_json["metadata"],
        storage_usage=response_json["storage_usage"]
    )
# See https://docs.vectara.com/docs/rest-api/query-corpus
def retrieve_chunks(query: str, limit: int = 10, filter_by_id: str = None) -> tuple[list[str], str]:
    """
    Retrieves relevant chunks and a generated summary from the Vectara corpus based on the query.

    Args:
        query (str): The user's query.
        limit (int): The maximum number of search results to return.
        filter_by_id (str, optional): An ID to filter documents. Defaults to None.

    Returns:
        tuple[list[str], str]: A tuple containing a list of retrieved text chunks and the llm generation.
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key
    
    metadata_filter = MetadataFilter().by_doc_id(filter_by_id).build() if filter_by_id else None
    
    search = {"limit": limit}
    if metadata_filter:
        search["metadata_filter"] = metadata_filter

    payload = {
        "query": query,
        "search": search,
        "generation": {
            "generation_preset_name": "mockingbird-2.0", # Using Mockingbird for RAG
            "max_used_search_results": 5,
            "response_language": "eng",
            "enable_factual_consistency_score": True,
            # "prompt_template": "[\n  {\"role\": \"system\", \"content\": \"You are a helpful search assistant.\"},\n  #foreach ($qResult in $vectaraQueryResults)\n     {\"role\": \"user\", \"content\": \"Given the $vectaraIdxWord[$foreach.index] search result.\"},\n     {\"role\": \"assistant\", \"content\": \"${qResult.getText()}\" },\n  #end\n  {\"role\": \"user\", \"content\": \"Generate a summary for the query '${vectaraQuery}' based on the above results.\"}\n]\n",
        },
        # NOTE: We can stream response
        "stream_response": False,
        "save_history": True,
        "intelligent_query_rewriting": False
    }

    endpoint = f"corpora/{CORPUS_KEY}/query"

    try:
        response_json = make_vectara_api_call("POST", endpoint, json=payload)
        pprint(response_json)
        
        retrieved_chunks = []

        # Extract search results (chunks)
        # The structure of the response has changed, adapt extraction logic
        if "search_results" in response_json:
            for search_result in response_json["search_results"]:
                if "text" in search_result:
                    retrieved_chunks.append(search_result["text"])
        
        
        # Extract generated summary
        if "summary" in response_json: # Changed from generation_response to summary
            generated_response = response_json["summary"] # Changed from generation_response["text"] to summary
            print(f"Factual Consistency Score: {response_json.get('factual_consistency_score')}") # Moved factual_consistency_score to top level
        else:
            generated_response = ""
            print("No generated response found in the Vectara response.")
        return retrieved_chunks, generated_response

    except VectaraAPIError as e:
        raise VectaraAPIError(f"Error querying Vectara: {e}") from e

def get_vectara_corpus_info(limit: int = 50, metadata_filter: str = None, page_key: str = None) -> dict:
    """
    Fetches documents from a specific Vectara corpus.
    
    Args:
        limit (int, optional): Maximum number of documents to return. Must be between 1 and 100. Defaults to 50.
        metadata_filter (str, optional): Filter documents by metadata. Uses expression similar to query metadata filter.
        page_key (str, optional): Key used to retrieve the next page of documents after the limit has been reached.
    
    Returns:
        dict: The response from the Vectara API containing the requested documents.
        
    Raises:
        VectaraAPIError: If there's an error with the Vectara API request.
    """
    CORPUS_KEY = "YouTwo"

    # Validate inputs
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")
    
    if len(CORPUS_KEY) > 50 or not all(c.isalnum() or c in ['_', '=', '-'] for c in CORPUS_KEY):
        raise ValueError("corpus_key must be <= 50 characters and match regex [a-zA-Z0-9_\\=\\-]+$")
    
    endpoint = f"corpora/{CORPUS_KEY}/documents"
    
    params = {}
    if limit is not None:
        params["limit"] = limit
    if metadata_filter is not None:
        params["metadata_filter"] = metadata_filter
    if page_key is not None:
        params["page_key"] = page_key
        
    try:
        return make_vectara_api_call("GET", endpoint, params=params)
    except VectaraAPIError as e:
        raise VectaraAPIError(f"Error fetching documents from Vectara corpus: {e}") from e

def fetch_document_by_id(document_id: str) -> dict:
    """
    Retrieves the content and metadata of a specific document by its ID.
    
    Args:
        document_id (str): The document ID to retrieve. Must be percent encoded.
        
    Returns:
        dict: The document data including content and metadata.
        
    Raises:
        VectaraAPIError: If there's an error with the Vectara API request.
    """
    from urllib.parse import quote
    
    CORPUS_KEY = "YouTwo"
    request_timeout = 20
    request_timeout_millis = 60000
    
    # Validate corpus key
    if len(CORPUS_KEY) > 50 or not all(c.isalnum() or c in ['_', '=', '-'] for c in CORPUS_KEY):
        raise ValueError("corpus_key must be <= 50 characters and match regex [a-zA-Z0-9_\\=\\-]+$")
    
    # Ensure document_id is percent encoded
    encoded_document_id = quote(document_id)
    
    endpoint = f"corpora/{CORPUS_KEY}/documents/{encoded_document_id}"
    
    headers = {}
    # Set timeout parameters if needed
    if request_timeout is not None:
        headers["Request-Timeout"] = str(request_timeout)
    if request_timeout_millis is not None:
        headers["Request-Timeout-Millis"] = str(request_timeout_millis)
        
    try:
        return make_vectara_api_call("GET", endpoint, headers=headers)
    except VectaraAPIError as e:
        raise VectaraAPIError(f"Error fetching document from Vectara: {e}") from e

# This is still a placeholder
def generate_llm_response(chat_state: list[dict], retrieved_chunks: list[str], summary: str) -> str:
    """
    Generates an LLM response based on chat state, retrieved chunks, and a generated summary.
    In this updated version, the summary from Vectara is directly used as the LLM response.

    Args:
        chat_state (list[dict]): The current conversation history/chat state (not directly used here but kept for signature consistency).
        retrieved_chunks (list[str]): The chunks retrieved from the RAG system (can be used for additional context if needed).
        summary (str): The summary generated by Vectara's RAG.

    Returns:
        str: The LLM's generated response (which is the Vectara summary).
    """
    print("Using Vectara generated summary as LLM response.")
    if summary:
        return summary
    else:
        # Fallback if for some reason summary is empty, though it shouldn't be with successful RAG
        context = "\n".join(retrieved_chunks)
        return f"Based on the retrieved information:\n{context}\n\nNo summary was generated, but here's the raw context."

def test_file_upload():
    # Change filepath
    FILEPATH = "~/Downloads/Linux-Essentials-Training-Course-craw-updated.pdf"
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv()

    try:
        pdf_path = Path(FILEPATH).expanduser()
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        upload_file_to_vectara(pdf_bytes, pdf_path.name)
    except Exception as e:
        raise IndexingError(f"Error occurred while uploading PDF: {e}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # chunks, summary = retrieve_chunks("What is the main idea of the document?")
    # print(chunks)
    # print(summary)
    docs = fetch_document_by_id('intro.md')
    pprint(docs)
    # save to json
    with open('intro.md.json', 'w') as f:
        json.dump(docs, f)