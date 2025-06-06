from ast import In
import os
import requests
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

def upload_pdf_to_vectara(pdf_bytes: bytes, filename: str) :
    """
    Uploads a PDF file to Vectara for processing.

    Args:
        pdf_bytes (bytes): The PDF file content in bytes.
        filename (str): The name of the PDF file.

    Returns:
        None

    Raises:
        VectaraAPIError: If there's an error during the Vectara API call.
        IndexingError: For other processing errors
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key

    # Check if pdf_bytes is provided
    if not pdf_bytes:
        raise IndexingError("No PDF bytes provided.")
    
    # Ensure valid filename
    if not filename.endswith(".pdf"):
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
        'file': (filename, pdf_bytes, 'application/pdf')
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Vectara API response:", response.json())
        # You might want to store some information from the Vectara response
        # in your session object, e.g., document ID.
    except requests.exceptions.RequestException as e:
        raise VectaraAPIError(f"Error uploading to Vectara: {e}") from e
    except Exception as e:
        raise VectaraAPIError(f"An unexpected error occurred during PDF upload: {e}") from e


def retrieve_chunks(query: str) -> list[str]:
    """
    Placeholder: Retrieves relevant chunks from the Vectara corpus based on the query.

    Args:
        query (str): The user's query.

    Returns:
        list[str]: A list of retrieved text chunks.
    """
    print(f"Retrieving chunks for query: '{query}'")
    # TODO: Implement actual Vectara query API call here
    # This will involve calling Vectara's query endpoint with the user's query
    # and processing the response to extract relevant text chunks.
    retrieved_chunks = [
        "Placeholder chunk 1: Information related to " + query,
        "Placeholder chunk 2: More details about " + query
    ]
    return retrieved_chunks


def generate_llm_response(chat_state: list[dict], retrieved_chunks: list[str]) -> str:
    """
    Placeholder: Generates an LLM response based on chat state and retrieved chunks.

    Args:
        chat_state (list[dict]): The current conversation history/chat state.
        retrieved_chunks (list[str]): The chunks retrieved from the RAG system.

    Returns:
        str: The LLM's generated response.
    """
    print("Generating LLM response...")
    # TODO: Implement LLM integration here
    # This will involve sending the chat_state and retrieved_chunks to an LLM (e.g., OpenAI, Llama, etc.)
    # to generate a coherent and contextually relevant response.
    context = "\n".join(retrieved_chunks)
    llm_response = f"Based on the retrieved information:\n{context}\n\nAnd your query, the answer is a placeholder response."
    return llm_response

def test_file_upload():
    # Change filepath
    FILEPATH = "~/Downloads/Linux-Essentials-Training-Course-craw-updated.pdf"
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv()

    def is_valid_pdf(path: str) -> bool:
        """Check if the path is a valid pdf."""
        return Path(path).expanduser().exists() and Path(path).expanduser().suffix == ".pdf"
    
    if not is_valid_pdf(FILEPATH):
        raise IndexingError(f"File {FILEPATH} does not exist or is not a PDF.")
    
    try:
        pdf_path = Path(FILEPATH).expanduser()
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        upload_pdf_to_vectara(pdf_bytes, pdf_path.name)
    except Exception as e:
        raise IndexingError(f"Error occurred while uploading PDF: {e}")