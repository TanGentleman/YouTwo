import asyncio
from smolagents import tool

from youtwo.memory.visualize import visualize_from_dict, visualize_knowledge_graph
from youtwo.paths import DATA_DIR
from youtwo.rag.vectara_client import VectaraClient
from youtwo.schemas import BriefEntity, BriefRelation, Observation
from youtwo.server.server import get_graph_data, initialize_mcp, run_convex_function
from youtwo.server.utils import async_convex_api_call, get_convex_url

DIRECT_HTTP = True

@tool
def retrieve_tool(
    query: str, limit: int = 5, filter_by_id: str | None = None
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

@tool
def view_graph() -> dict:
    """
    Get the graph data.

    Returns:
        A list of graph data.
    """

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        asyncio.run(async_convex_api_call("graph", "GET", deployment_url=direct_url))
    else:
        deployment_info = asyncio.run(initialize_mcp())
        return asyncio.run(get_graph_data(deployment_info))

@tool
def visualize_live_graph() -> bool:
    """
    Visualize the knowledge graph from the database.
    
    Returns:
        bool: True if successful
    """
    asyncio.run(visualize_knowledge_graph())
    return True

@tool
def visualize_custom_graph(graph_data: dict) -> bool:
    """
    Visualize a knowledge graph from provided data.
    
    Args:
        graph_data (dict): A dictionary containing entities and relations to visualize.
                          Should have the structure:
                          {
                              "entities": [{"name": str, "entityType": str}],
                              "relations": [{"from": str, "relationType": str, "to": str}]
                          }
    
    Returns:
        bool: True if successful
    """
    asyncio.run(visualize_from_dict(graph_data))
    return True

def correct_relation_format(relations: list[BriefRelation]) -> list[BriefRelation]:
    return [
        {"from": relation["source"],
         "relationType": relation["relationType"],
         "to": relation["target"]}
        for relation in relations]

@tool
def get_entities() -> list[BriefEntity]:
    """
    Get all entities.

    Returns:
        list[BriefEntity]: A list of entities, where each BriefEntity contains:
            - name (str): The entity name
            - entityType (str): The type/category of the entity
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    result = asyncio.run(run_convex_function(MCP_KEY, "entities:getBriefEntities", {}))
    return result


@tool
def create_entities(entities: list[BriefEntity]) -> dict | None:
    """
    Create new entities.

    Args:
        entities (list[BriefEntity]): A list of entities to create. Each BriefEntity must contain:
            - name (str): The entity name
            - entityType (str): The type/category of the entity

    Returns:
        dict | None: A dictionary of the created entities, or None if creation failed.
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "entities:createEntities", {"entities": entities}
    ))


@tool
def delete_entities(entity_names: list[str]) -> dict | None:
    """
    Delete entities by name.

    Args:
        entity_names (list[str]): A list of entity names to delete.

    Returns:
        dict | None: A dictionary of the deleted entities, or None if deletion failed.
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "entities:deleteEntities", {"entityNames": entity_names}
    ))


@tool
def create_relations(relations: list[BriefRelation]) -> dict | None:
    """
    Create relations between existing entities.

    Args:
        relations (list[BriefRelation]): A list of relations to create. Each BriefRelation must contain:
            - source (str): The name of the source entity
            - relationType (str): The type of relationship
            - target (str): The name of the target entity

    Returns:
        dict | None: A dictionary of the created relations, or None if creation failed.
    """
    relations = correct_relation_format(relations)
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "relations:createRelations", {"relations": relations}
    ))

@tool
def delete_relations(relations: list[BriefRelation]) -> dict | None:
    """
    Delete relations between entities.

    Args:
        relations (list[BriefRelation]): A list of relations to delete. Each BriefRelation must contain:
            - source (str): The name of the source entity
            - relationType (str): The type of relationship
            - target (str): The name of the target entity

    Returns:
        dict | None: A dictionary of the deleted relations, or None if deletion failed.
    """
    relations = correct_relation_format(relations)
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "relations:deleteRelations", {"relations": relations}
    ))

@tool
def add_observations(observations: list[Observation]) -> dict | None:
    """
    Add observations to existing entities.

    Args:
        observations (list[Observation]): A list of observations to add. Each Observation must contain:
            - entityName (str): The name of the entity to add observations to
            - contents (list[str]): A list of observation content strings

    Returns:
        dict | None: A dictionary of the added observations, or None if addition failed.
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "entities:addObservations", {"observations": observations}
    ))

@tool
def delete_observations(observations: list[Observation]) -> dict | None:
    """
    Delete observations from existing entities.

    Args:
        observations (list[Observation]): A list of observations to delete. Each Observation must contain:
            - entityName (str): The name of the entity to delete observations from
            - contents (list[str]): A list of observation content strings to remove

    Returns:
        dict | None: A dictionary of the deleted observations, or None if deletion failed.
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(
        MCP_KEY, "entities:deleteObservations", {"observations": observations}
    ))

@tool
def get_graph() -> dict | None:
    """
    Read the graph of the knowledge base.

    Returns:
        dict | None: A dictionary containing the knowledge graph structure, or None if retrieval failed.
    """
    deployment_info = asyncio.run(initialize_mcp())
    MCP_KEY = deployment_info["deploymentSelector"]
    return asyncio.run(run_convex_function(MCP_KEY, "knowledge:readGraph", {}))

# @tool
# def save_graph_as_image(graph_data: dict) -> dict:
#     """
#     Save the graph as an image and return it in MCP-compliant format.
    
#     Args:
#         graph_data: Dictionary containing the graph data to visualize
        
#     Returns:
#         dict: MCP-compliant image content with base64-encoded data
#     """
#     # First, visualize the graph to create the image file
#     asyncio.run(visualize_from_dict(graph_data))
    
#     image_filepath = DATA_DIR / "knowledge_graph.png"
#     assert image_filepath.exists(), "Graph image not found"
#     # TODO: Return the image conforming to MCP spec
#     return None

if __name__ == "__main__":
    view_graph()
