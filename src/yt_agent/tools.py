from smolagents import tool
from src.schemas import VectaraDocuments
from src.yt_rag.rag import get_vectara_corpus_info, retrieve_chunks

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
def inspect_database_tool() -> str:
    """
    Inspect the vector database

    Returns:
        A list of documents
    """
    results = get_vectara_corpus_info(limit = 50)
    documents = VectaraDocuments(documents = results["documents"])
    id_list = [document["id"] for document in documents["documents"]]
    final_string = "The following documents IDs are in the vector database:\n"
    for i, id in enumerate(id_list):
        final_string += f"{i+1}. {id}\n"
    return final_string
