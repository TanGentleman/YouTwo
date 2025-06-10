from smolagents import tool
from src.yt_rag.rag import retrieve_chunks

@tool
def retrieve_tool(query: str, limit: int = 5) -> list[dict]:
    """
    Retrieve chunks by relevance to a query

    Args:
        query: The query to retrieve chunks for
        limit: The maximum number of chunks to retrieve (default: 5)

    Returns:
        A list of chunks
    """
    return retrieve_chunks(query, limit)