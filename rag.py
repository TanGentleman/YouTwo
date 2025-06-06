import os
import requests

def upload_pdf_to_vectara(pdf_bytes: bytes, filename: str) :
    """
    Uploads a PDF file to Vectara for processing.

    Args:
        pdf_bytes (bytes): The PDF file content in bytes.

    Returns:
        None
    """
    CORPUS_KEY = "YouTwo"  # Replace with your actual corpus key

    # Check if pdf_bytes is provided
    if not pdf_bytes:
        print("No PDF bytes provided.")
        return
    
    # Ensure valid filename
    if not filename.endswith(".pdf"):
        print("Invalid filename. Please provide a filename ending with .pdf")
        return

    # Replace with your actual corpus_key and API key
    api_key = os.getenv("VECTARA_API_KEY")
    if not api_key:
        print("Vectara API key not set. Please set the VECTARA_API_KEY environment variable.")
        return
    url = f"https://api.vectara.io/v2/corpora/{CORPUS_KEY}/upload_file"

    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }

    # You can add metadata, chunking_strategy, table_extraction_config here
    # For example:
    # metadata = json.dumps({"session_id": session_id})
    # files = {
    #     'file': (f'{session_id}.pdf', pdf_bytes, 'application/pdf'),
    #     'metadata': (None, metadata, 'application/json')
    # }

    files = {
        'file': (filename, pdf_bytes, 'application/pdf')
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Vectara API response:", response.json())
        pdf_embedded = True  # Set to True if the upload was successful
        # You might want to store some information from the Vectara response
        # in your session object, e.g., document ID.
    except requests.exceptions.RequestException as e:
        print(f"Error uploading to Vectara: {e}")
        # Handle the error appropriately, e.g., log it, notify user

if __name__ == "__main__":
    # Example usage
    from pathlib import Path
    FILEPATH = Path("~/Downloads/drama-therapy-paper.pdf").expanduser()
    assert FILEPATH.exists(), f"File {FILEPATH} does not exist."
    assert FILEPATH.suffix == ".pdf", f"File {FILEPATH} is not a PDF." 
    with open(FILEPATH, "rb") as f:
        pdf_bytes = f.read()
    upload_pdf_to_vectara(pdf_bytes, FILEPATH.name)