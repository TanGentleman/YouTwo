import asyncio
import logging
from typing import Any

from mcp import types
from mcp.server.fastmcp import FastMCP

from youtwo.schemas import BriefEntity, BriefRelation, Observation
from youtwo.server.server import get_function_spec, initialize_mcp, run_convex_function

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("YouTwo MCP")
deployment_info = asyncio.run(initialize_mcp())
if not deployment_info:
    print("No deployment found")
    exit(1)
MCP_KEY = deployment_info["deploymentSelector"]


def correct_relation_format(relations: list[BriefRelation]) -> list[BriefRelation]:
    return [
        {"from": relation["source"],
         "relationType": relation["relationType"],
         "to": relation["target"]}
        for relation in relations]

@app.tool()
async def get_entities() -> list[BriefEntity]:
    """
    Get all entities.
    """
    result = await run_convex_function(MCP_KEY, "entities:getBriefEntities", {})
    return result


@app.tool()
async def create_entities(entities: list[BriefEntity]) -> Any:
    """
    Create new entities.
    """
    return await run_convex_function(
        MCP_KEY, "entities:createEntities", {"entities": entities}
    )


@app.tool()
async def delete_entities(entity_names: list[str]) -> Any:
    """
    Delete entities by name.
    """
    return await run_convex_function(
        MCP_KEY, "entities:deleteEntities", {"entityNames": entity_names}
    )


@app.tool()
async def create_relations(relations: list[BriefRelation]) -> Any:
    """
    Create relations between existing entities.
    """
    relations = correct_relation_format(relations)
    return await run_convex_function(
        MCP_KEY, "relations:createRelations", {"relations": relations}
    )

@app.tool()
async def delete_relations(relations: list[BriefRelation]) -> Any:
    """
    Delete relations between entities.
    """
    relations = correct_relation_format(relations)
    return await run_convex_function(
        MCP_KEY, "relations:deleteRelations", {"relations": relations}
    )

@app.tool()
async def add_observations(observations: list[Observation]) -> Any:
    """
    Add observations to existing entities.
    """
    return await run_convex_function(
        MCP_KEY, "entities:addObservations", {"observations": observations}
    )

@app.tool()
async def delete_observations(observations: list[Observation]) -> Any:
    """
    Delete observations from existing entities.
    """
    return await run_convex_function(
        MCP_KEY, "entities:deleteObservations", {"observations": observations}
    )

@app.tool()
async def get_graph() -> Any:
    """
    Read the graph of the knowledge base.
    """
    return await run_convex_function(MCP_KEY, "knowledge:readGraph", {})


@app.tool()
async def get_tools() -> list[types.Tool]:
    """
    Get a list of available tools and their specifications.
    """
    return await get_function_spec(deployment_info)

# @app.call_tool()
# async def call_tool(
#     name: str,
#     arguments: dict
# ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
#     try:
#         return await run_convex_function(deployment_info["deploymentSelector"], name, arguments)
#     except Exception as e:
#         print(f"Error running tool {name}: {e}")
#         return None

if __name__ == "__main__":
    app.run()
