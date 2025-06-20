import json
import logging
import os
from pathlib import Path
from typing import List, Tuple
from urllib.parse import quote

import requests
from typing_extensions import TypedDict

from youtwo.exceptions import IndexingError
from youtwo.schemas import UploadResult, VectaraDoc
from youtwo.utils import save_dict_to_file

logger = logging.getLogger(__name__)


class VectaraAPIError(Exception):
    """Custom exception for Vectara API errors."""

    pass


class UploadFileInputSchema(TypedDict):
    file: bytes
    filename: str
    metadata: dict


class MetadataFilter:
    """
    A helper class to build metadata filter strings for Vectara queries.

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


def is_allowed_filetype(suffix: str) -> bool:
    """
    Check if the file type is allowed for upload to Vectara.

    Args:
        suffix (str): The file extension including the dot (e.g., '.pdf')

    Returns:
        bool: True if the file type is allowed, False otherwise
    """
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
    return suffix.lower() in [
        ".md",
        ".pdf",
        ".odt",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".txt",
        ".html",
        ".lxml",
        ".rtf",
        ".epub",
    ]


def process_upload_response(response_json: dict) -> UploadResult:
    """
    Processes the Vectara API response after a file upload.

    Args:
        response_json (dict): The Vectara API response.

    Returns:
        UploadResult: The upload result.
    """
    save_dict_to_file(response_json, "upload_results.json")

    return UploadResult(
        id=response_json["id"],
        metadata=response_json["metadata"],
        storage_usage=response_json["storage_usage"],
    )


class VectaraClient:
    """
    Client for interacting with Vectara API.

    This class provides methods for all Vectara operations including:
    - Uploading files
    - Retrieving chunks based on queries
    - Managing corpus information
    - Fetching documents by ID
    """

    def __init__(self, corpus_key: str = None, api_key: str = None):
        """
        Initialize the VectaraClient.

        Args:
            corpus_key (str, optional): The Vectara corpus key. If not provided, looks for VECTARA_CORPUS_KEY env var.
            api_key (str, optional): The Vectara API key. If not provided, looks for VECTARA_API_KEY env var.
        """
        self.base_url = "https://api.vectara.io/v2"

        # Load environment variables if needed
        if api_key is None:
            from dotenv import load_dotenv

            load_dotenv()
            api_key = os.getenv("VECTARA_API_KEY")

        if corpus_key is None:
            corpus_key = os.getenv("VECTARA_CORPUS_KEY", "YouTwo")

        self.corpus_key = corpus_key
        self.api_key = api_key

        if not self.api_key:
            raise VectaraAPIError(
                "Vectara API key not set. Please provide api_key or set the VECTARA_API_KEY environment variable."
            )

    def _make_api_call(self, method: str, endpoint: str, **kwargs) -> dict:
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
        url = f"{self.base_url}/{endpoint}"

        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Accept": "application/json",
                "x-api-key": self.api_key,
            }
        )

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()
        except requests.exceptions.RequestException as e:
            raise VectaraAPIError(
                f"Error calling Vectara API endpoint {endpoint}: {e}"
            ) from e
        except json.JSONDecodeError:
            raise VectaraAPIError(
                f"Error decoding JSON response from Vectara API endpoint {endpoint}: {response.text}"
            )
        except Exception as e:
            raise VectaraAPIError(
                f"An unexpected error occurred during Vectara API call: {e}"
            ) from e

    def upload_file(self, file_bytes: bytes, filename: str) -> UploadResult:
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
        # Check if file_bytes is provided
        if not file_bytes:
            raise IndexingError("No file bytes provided.")

        suffix = Path(filename).suffix
        # Ensure valid filename
        if not is_allowed_filetype(suffix):
            raise IndexingError(
                f"Invalid file type: {suffix}. Please provide a supported file type."
            )

        endpoint = f"corpora/{self.corpus_key}/upload_file"
        files = {"file": (filename, file_bytes)}

        try:
            response_json = self._make_api_call("POST", endpoint, files=files)
            result = process_upload_response(response_json)
            return result
        except VectaraAPIError as e:
            raise VectaraAPIError(
                f"Error uploading file '{filename}' to Vectara: {e}"
            ) from e

    def retrieve_chunks(
        self, query: str, limit: int = 10, filter_by_id: str = None
    ) -> Tuple[List[str], str]:
        """
        Retrieves relevant chunks and a generated summary from the Vectara corpus based on the query.

        Args:
            query (str): The user's query.
            limit (int): The maximum number of search results to return.
            filter_by_id (str, optional): An ID to filter documents. Defaults to None.

        Returns:
            tuple[list[str], str]: A tuple containing a list of retrieved text chunks and the llm generation.
        """
        metadata_filter = (
            MetadataFilter().by_doc_id(filter_by_id).build() if filter_by_id else None
        )

        search = {"limit": limit}
        if metadata_filter:
            search["metadata_filter"] = metadata_filter

        payload = {
            "query": query,
            "search": search,
            "generation": {
                "generation_preset_name": "mockingbird-2.0",  # Using Mockingbird for RAG
                "max_used_search_results": 5,
                "response_language": "eng",
                "enable_factual_consistency_score": True,
            },
            "stream_response": False,
            "save_history": True,
            "intelligent_query_rewriting": False,
        }

        endpoint = f"corpora/{self.corpus_key}/query"

        try:
            response_json = self._make_api_call("POST", endpoint, json=payload)
            logger.debug(f"Vectara response: {response_json}")

            retrieved_chunks = []

            # Extract search results (chunks)
            if "search_results" in response_json:
                for search_result in response_json["search_results"]:
                    if "text" in search_result:
                        retrieved_chunks.append(search_result["text"])

            # Extract generated summary
            if "summary" in response_json:
                generated_response = response_json["summary"]
                logger.info(
                    f"Factual Consistency Score: {response_json.get('factual_consistency_score')}"
                )
            else:
                generated_response = ""
                logger.warning("No generated response found in the Vectara response.")
            return retrieved_chunks, generated_response

        except VectaraAPIError as e:
            raise VectaraAPIError(f"Error querying Vectara: {e}") from e

    def get_corpus_info(
        self, limit: int = 50, metadata_filter: str = None, page_key: str = None
    ) -> list[VectaraDoc]:
        """
        Fetches documents from a specific Vectara corpus.

        Args:
            limit (int, optional): Maximum number of documents to return. Must be between 1 and 100. Defaults to 50.
            metadata_filter (str, optional): Filter documents by metadata. Uses expression similar to query metadata filter.
            page_key (str, optional): Key used to retrieve the next page of documents after the limit has been reached.

        Returns:
            list[VectaraDoc]: The response from the Vectara API containing the requested documents.

        Raises:
            VectaraAPIError: If there's an error with the Vectara API request.
        """
        # Validate inputs
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        if len(self.corpus_key) > 50 or not all(
            c.isalnum() or c in ["_", "=", "-"] for c in self.corpus_key
        ):
            raise ValueError(
                "corpus_key must be <= 50 characters and match regex [a-zA-Z0-9_\\=\\-]+$"
            )

        endpoint = f"corpora/{self.corpus_key}/documents"

        params = {}
        if limit is not None:
            params["limit"] = limit
        if metadata_filter is not None:
            params["metadata_filter"] = metadata_filter
        if page_key is not None:
            params["page_key"] = page_key

        try:
            response = self._make_api_call("GET", endpoint, params=params)
            return response["documents"]
        except VectaraAPIError as e:
            raise VectaraAPIError(
                f"Error fetching documents from Vectara corpus: {e}"
            ) from e

    def get_filenames(self, limit: int = 50) -> List[str]:
        """
        Retrieves the filenames of all documents in the Vectara corpus.

        Args:
            limit (int): Maximum number of documents to return.

        Returns:
            List[str]: List of document IDs.
        """
        documents = self.get_corpus_info(limit=limit)
        id_list = [document["id"] for document in documents]
        return id_list

    def fetch_document_by_id(self, document_id: str) -> dict:
        """
        Retrieves the content and metadata of a specific document by its ID.

        Args:
            document_id (str): The document ID to retrieve. Will be percent encoded.

        Returns:
            dict: The document data including content and metadata.

        Raises:
            VectaraAPIError: If there's an error with the Vectara API request.
        """
        # Ensure document_id is percent encoded
        encoded_document_id = quote(document_id)

        endpoint = f"corpora/{self.corpus_key}/documents/{encoded_document_id}"

        headers = {"Request-Timeout": "20", "Request-Timeout-Millis": "60000"}

        try:
            return self._make_api_call("GET", endpoint, headers=headers)
        except VectaraAPIError as e:
            raise VectaraAPIError(f"Error fetching document from Vectara: {e}") from e


if __name__ == "__main__":
    client = VectaraClient()
    filenames = client.get_filenames(limit=1)
    if not filenames:
        print("No documents found")
        exit()

    first_file = filenames[0]
    metadata_filter = MetadataFilter().by_doc_id(first_file).build()
    print("Testing metadata_filter:", metadata_filter)
    docs = client.get_corpus_info(limit=1, metadata_filter=metadata_filter)
    assert first_file == docs[0]["id"]
    print("Success!")
