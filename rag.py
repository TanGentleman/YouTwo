import json
import logging
import os
from pathlib import Path
import requests
from pprint import pprint
from schemas import UploadResult

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
    return suffix in [".pdf", ".odt", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".html", ".lxml", ".rtf", ".epub"]

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
        None

    Raises:
        VectaraAPIError: If there's an error during the Vectara API call.
        IndexingError: For other processing errors
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key

    # Check if file_bytes is provided
    if not file_bytes:
        raise IndexingError("No file bytes provided.")
    
    suffix = Path(filename).suffix
    # Ensure valid filename
    if not is_allowed_filetype(suffix):
        raise IndexingError("Invalid filename. Please provide a filename ending with .pdf")

    # Replace with your actual corpus_key and API key
    api_key = os.getenv("VECTARA_API_KEY")
    if not api_key:
        raise IndexingError("Vectara API key not set. Please set the VECTARA_API_KEY environment variable.")
    url = f"https://api.vectara.io/v2/corpora/{CORPUS_KEY}/upload_file"

    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    files = {
        'file': (filename, file_bytes)
    }


    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_json = response.json()
        
        result = process_upload_response(response_json)
        # You might want to store some information from the Vectara response
        # in your session object, e.g., document ID.
        return result
    except requests.exceptions.RequestException as e:
        raise VectaraAPIError(f"Error uploading to Vectara: {e}") from e
    except Exception as e:
        raise VectaraAPIError(f"An unexpected error occurred during PDF upload: {e}") from e


def process_upload_response(response_json: dict) -> UploadResult:
    """
    Stores 

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
def retrieve_chunks(query: str, limit: int = 10) -> tuple[list[str], str]:
    """
    Retrieves relevant chunks and a generated summary from the Vectara corpus based on the query.

    Args:
        query (str): The user's query.

    Returns:
        tuple[list[str], str]: A tuple containing a list of retrieved text chunks and the llm generation.
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key
    api_key = os.getenv("VECTARA_API_KEY")
    if not api_key:
        raise IndexingError("Vectara API key not set. Please set the VECTARA_API_KEY environment variable.")

    url = f"https://api.vectara.io/v2/corpora/{CORPUS_KEY}/query"
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search": {
            "limit": limit,  # Number of search results to retrieve
            # "reranker": {
            #     "type": "customer_reranker",
            #     "reranker_name": "Rerank_Multilingual_v1",
            #     "limit": 0,
            #     "cutoff": 0,
            #     "include_context": True
            # }
        },
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

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()
        pprint(response_json)
        # TODO: Parse Output here
        
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

    except requests.exceptions.RequestException as e:
        raise VectaraAPIError(f"Error querying Vectara: {e}") from e
    except Exception as e:
        raise VectaraAPIError(f"An unexpected error occurred during Vectara query: {e}") from e


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
    chunks, summary = retrieve_chunks("What is the main idea of the document?")
    print(chunks)
    print(summary)