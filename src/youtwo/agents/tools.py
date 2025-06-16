from smolagents import tool

from youtwo.rag.vectara_client import VectaraClient
from youtwo.server.server import get_graph_data, initialize_mcp


@tool
def retrieve_tool(
    query: str, limit: int = 5, filter_by_id: str = None
) -> dict[str, list[str] | str]:
    """
    Retrieve chunks by relevance to a query

    Args:
        query: The query to retrieve chunks for
        limit: The maximum number of chunks to retrieve (default: 5)
        filter_by_id: A document ID to filter by
    Returns:
        A list of chunks, and a grounded summary
    """
    client = VectaraClient()
    chunks, vectara_summary = client.retrieve_chunks(query, limit, filter_by_id)
    return {"chunks": chunks, "summary": vectara_summary}


@tool
def inspect_database_tool() -> list[str]:
    """
    Inspect the vector database.

    Returns:
        A list of all document IDs (filenames) in the database.
    """
    client = VectaraClient()
    id_list = client.get_filenames()
    return id_list


def ensure_convex_site_url() -> str:
    from os import getenv
    from dotenv import load_dotenv
    load_dotenv()
    direct_url = getenv("CONVEX_SITE_URL")
    if not direct_url:
        raise ValueError("CONVEX_SITE_URL must be set to view the graph")
    return direct_url


@tool
def view_graph() -> list[dict]:
    """
    Get the graph data.

    Returns:
        A list of graph data.
    """
    import asyncio

    # If instead using HTTP with a site url, use environment
    DIRECT_HTTP = True
    if DIRECT_HTTP:
        direct_url = ensure_convex_site_url()
        deployment_info = {"deploymentSelector": None, "url": direct_url}
    else:
        deployment_info = asyncio.run(initialize_mcp())
    return asyncio.run(get_graph_data(deployment_info))


if __name__ == "__main__":
    print(view_graph())
