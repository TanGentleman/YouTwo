from smolagents import tool
from src.yt_rag.rag import retrieve_chunks

@tool
def retrieve_tool(query: str, limit: int = 5) -> dict[str, list[str] | str]:
    """
    Retrieve chunks by relevance to a query

    Args:
        query: The query to retrieve chunks for
        limit: The maximum number of chunks to retrieve (default: 5)

    Returns:
        A list of chunks, and a grounded summary
    """
    chunks, vectara_summary = retrieve_chunks(query, limit)
    return {
        "chunks": chunks,
        "summary": vectara_summary
    }