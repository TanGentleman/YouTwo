import asyncio
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from smolagents import tool

from youtwo.memory.visualize import visualize_from_dict, visualize_knowledge_graph
from youtwo.rag.vectara_client import VectaraClient
from youtwo.schemas import BriefEntity, BriefRelation, Observation
from youtwo.server.server import get_graph_data, initialize_mcp, run_convex_function
from youtwo.server.utils import async_convex_api_call, get_convex_url

DIRECT_HTTP = True


# Input validation schemas
class RetrieveToolInput(BaseModel):
    query: str = Field(
        ..., min_length=1, description="The query to retrieve chunks for"
    )
    limit: int = Field(
        default=5, ge=1, le=100, description="Maximum number of chunks to retrieve"
    )
    filter_by_id: Optional[str] = Field(
        default=None, description="A document ID to filter by"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class CreateEntitiesInput(BaseModel):
    entities: list[BriefEntity] = Field(
        ..., min_length=1, description="List of entities to create"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class DeleteEntitiesInput(BaseModel):
    entity_names: list[str] = Field(
        ..., min_length=1, description="List of entity names to delete"
    )

    @field_validator("entity_names")
    def validate_entity_names(cls, v):
        if not all(isinstance(name, str) for name in v):
            raise ValueError("All entity names must be non-empty strings")
        return v

    def to_dict(self) -> dict:
        return self.model_dump()


class CreateRelationsInput(BaseModel):
    relations: list[BriefRelation] = Field(
        ..., min_length=1, description="List of relations to create"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class DeleteRelationsInput(BaseModel):
    relations: list[BriefRelation] = Field(
        ..., min_length=1, description="List of relations to delete"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class AddObservationsInput(BaseModel):
    observations: list[Observation] = Field(
        ..., min_length=1, description="List of observations to add"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class DeleteObservationsInput(BaseModel):
    observations: list[Observation] = Field(
        ..., min_length=1, description="List of observations to delete"
    )

    def to_dict(self) -> dict:
        return self.model_dump()


class VisualizeCustomGraphInput(BaseModel):
    graph_data: dict = Field(
        ..., description="Dictionary containing entities and relations to visualize"
    )

    @field_validator("graph_data")
    def validate_graph_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError("graph_data must be a dictionary")
        if "entities" not in v or "relations" not in v:
            raise ValueError("graph_data must contain 'entities' and 'relations' keys")
        if not isinstance(v["entities"], list) or not isinstance(v["relations"], list):
            raise ValueError("entities and relations must be lists")
        return v

    def to_dict(self) -> dict:
        return self.model_dump()


def correct_relation_format(relations: list[BriefRelation]) -> list[BriefRelation]:
    return [
        {
            "from": relation["source"],
            "relationType": relation["relationType"],
            "to": relation["target"],
        }
        for relation in relations
    ]


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
    # Validate inputs using Pydantic schema
    RetrieveToolInput(query=query, limit=limit, filter_by_id=filter_by_id)

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
def get_graph() -> dict:
    """
    Retrieve the active entities and relations from the database.

    Returns:
        A dictionary containing entities and relations. Relations have "from" and "to" keys
        indicating the source and target entities.
    """

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call("graph", "GET", deployment_url=direct_url)
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        return asyncio.run(get_graph_data(deployment_info))["graph"]


@tool
def visualize_live_graph() -> bool:
    """
    Display a visual representation of the entities and relations in the database.

    Opens in your default image viewer or browser.
    """

    asyncio.run(visualize_knowledge_graph(max_nodes=200, max_edges=200))
    return True


@tool
def visualize_custom_graph(graph_data: dict) -> bool:
    """
    Visualize a knowledge graph from provided data.

    This tool creates an interactive visual diagram from the provided graph data
    and displays it in your default image viewer. Max nodes and edges are 200.

    Args:
        graph_data (dict): A dictionary containing entities and relations to visualize.
                          Should have the structure:
                          {
                              "entities": [{"name": str, "entityType": str}],
                              "relations": [{"from": str, "relationType": str, "to": str}]
                          }
    """
    # Validate inputs using Pydantic schema
    VisualizeCustomGraphInput(graph_data=graph_data)

    asyncio.run(visualize_from_dict(graph_data))
    return True


@tool
def get_entities() -> list[BriefEntity]:
    """
    Get all entities.
    """
    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call("entities", "GET", deployment_url=direct_url)
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        result = asyncio.run(
            run_convex_function(MCP_KEY, "entities:getBriefEntities", {})
        )
        return result


@tool
def create_entities(entities: list[BriefEntity]) -> dict | None:
    """
    Create new entities.

    Args:
        entities (list[BriefEntity]): A list of entities to create. Each BriefEntity must contain:
            - name (str): The entity name
            - entityType (str): The type/category of the entity
    """
    # Validate inputs using Pydantic schema
    CreateEntitiesInput(entities=entities)

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "entities",
                "POST",
                data={"entities": entities},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "entities:createEntities", {"entities": entities}
            )
        )


@tool
def delete_entities(entity_names: list[str]) -> dict | None:
    """
    Delete entities by name.

    Args:
        entity_names (list[str]): A list of entity names to delete.

    Returns:
        dict | None: A dictionary of the deleted entities, or None if deletion failed.
    """
    # Validate inputs using Pydantic schema
    DeleteEntitiesInput(entity_names=entity_names)

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "entities",
                "DELETE",
                data={"entityNames": entity_names},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "entities:deleteEntities", {"entityNames": entity_names}
            )
        )


@tool
def create_relations(relations: list[BriefRelation]) -> dict | None:
    """
    Create relations between existing entities.

    Args:
        relations (list[BriefRelation]): A list of relations to create. Each BriefRelation must contain:
            - source (str): The name of the source entity
            - relationType (str): The type of relationship
            - target (str): The name of the target entity
    """
    # Validate inputs using Pydantic schema
    CreateRelationsInput(relations=relations)

    relations = correct_relation_format(relations)
    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "relations",
                "POST",
                data={"relations": relations},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "relations:createRelations", {"relations": relations}
            )
        )


@tool
def delete_relations(relations: list[BriefRelation]) -> dict | None:
    """
    Delete relations between entities.

    Args:
        relations (list[BriefRelation]): A list of relations to delete. Each BriefRelation must contain:
            - source (str): The name of the source entity
            - relationType (str): The type of relationship
            - target (str): The name of the target entity
    """
    # Validate inputs using Pydantic schema
    DeleteRelationsInput(relations=relations)

    relations = correct_relation_format(relations)
    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "relations",
                "DELETE",
                data={"relations": relations},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "relations:deleteRelations", {"relations": relations}
            )
        )


@tool
def add_observations(observations: list[Observation]) -> dict | None:
    """
    Add observations to existing entities.

    Args:
        observations (list[Observation]): A list of observations to add. Each Observation must contain:
            - entityName (str): The name of the entity to add observations to
            - contents (list[str]): A list of observation content strings
    """
    # Validate inputs using Pydantic schema
    AddObservationsInput(observations=observations)

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "observations",
                "POST",
                data={"observations": observations},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "entities:addObservations", {"observations": observations}
            )
        )


@tool
def delete_observations(observations: list[Observation]) -> dict | None:
    """
    Delete observations from existing entities.

    Args:
        observations (list[Observation]): A list of observations to delete. Each Observation must contain:
            - entityName (str): The name of the entity to delete observations from
            - contents (list[str]): A list of observation content strings to remove
    """
    # Validate inputs using Pydantic schema
    DeleteObservationsInput(observations=observations)

    if DIRECT_HTTP:
        direct_url = get_convex_url()
        return asyncio.run(
            async_convex_api_call(
                "observations",
                "DELETE",
                data={"deletions": observations},
                deployment_url=direct_url,
            )
        )
    else:
        deployment_info = asyncio.run(initialize_mcp())
        MCP_KEY = deployment_info["deploymentSelector"]
        return asyncio.run(
            run_convex_function(
                MCP_KEY, "entities:deleteObservations", {"observations": observations}
            )
        )


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
    get_graph()
