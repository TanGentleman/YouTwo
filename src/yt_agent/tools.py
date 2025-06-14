from smolagents import tool
from src.yt_rag.rag import get_filenames_from_vectara, retrieve_chunks

@tool
def retrieve_tool(query: str, limit: int = 5, filter_by_id: str = None) -> dict[str, list[str] | str]:
    """
    Retrieve chunks by relevance to a query

    Args:
        query: The query to retrieve chunks for
        limit: The maximum number of chunks to retrieve (default: 5)
        filter_by_id: A document ID to filter by
    Returns:
        A list of chunks, and a grounded summary
    """
    chunks, vectara_summary = retrieve_chunks(query, limit, filter_by_id)
    return {
        "chunks": chunks,
        "summary": vectara_summary
    }

@tool
def inspect_database_tool() -> list[str]:
    """
    Inspect the vector database.

    Returns:
        A list of all document IDs (filenames) in the database.
    """
    id_list = get_filenames_from_vectara()
    return id_list
