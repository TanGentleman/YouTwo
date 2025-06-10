from smolagents import tool
from src.schemas import VectaraDocuments
from src.yt_rag.rag import fetch_documents_from_corpus, retrieve_chunks

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

@tool
def inspect_vector_database() -> dict[str, list[str]]:
    """
    Inspect the vector database
    """
    results = fetch_documents_from_corpus(limit = 50)
    documents = VectaraDocuments(documents = results["documents"])
    return {
        "documents": documents["documents"],
    }
