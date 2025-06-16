import asyncio
import logging
from typing import Any

from mcp import types
from mcp.server.fastmcp import FastMCP

from youtwo.schemas import BriefEntity, BriefRelation
from youtwo.server.config import CONVEX_FUNCTION_MAP
from youtwo.server.server import get_function_spec, initialize_mcp, run_convex_function


def get_function_description(function_name: str) -> str:
    if function_name in CONVEX_FUNCTION_MAP:
        return CONVEX_FUNCTION_MAP[function_name]
    else:
        raise ValueError(f"Unknown function: {function_name}")


def get_tools() -> None | list[types.Tool]:
    deployment_info = asyncio.run(initialize_mcp())
    if not deployment_info:
        print("No deployment found")
        return
    function_spec = asyncio.run(get_function_spec(deployment_info))
    tools = []
    for func in function_spec:
        function_name = func["identifier"]
        function_type = func["functionType"]
        function_args = func["args"]
        print("Function: ", function_name, "Type: ", function_type)
        print("Args: ", function_args)
        print("--------------------------------")
        tools.append(
            types.Tool(
                name=function_name,
                description=get_function_description(function_name),
                inputSchema=function_args,
            )
        )
    return tools


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("YouTwo MCP")
deployment_info = asyncio.run(initialize_mcp())
if not deployment_info:
    print("No deployment found")
    exit(1)
MCP_KEY = deployment_info["deploymentSelector"]


@app.tool()
async def get_entities() -> list[BriefEntity]:
    return await run_convex_function(MCP_KEY, "entities:getBriefEntities", {})


@app.tool()
async def create_entities(entities: list[BriefEntity]) -> Any:
    return await run_convex_function(
        MCP_KEY, "entities:createEntities", {"entities": entities}
    )


@app.tool()
async def delete_entities(entity_names: list[str]) -> Any:
    return await run_convex_function(
        MCP_KEY, "entities:deleteEntities", {"entityNames": entity_names}
    )


@app.tool()
async def create_relations(relations: list[BriefRelation]) -> Any:
    return await run_convex_function(
        MCP_KEY, "relations:createRelations", {"relations": relations}
    )


@app.tool()
async def delete_relations(relations: list[BriefRelation]) -> Any:
    return await run_convex_function(
        MCP_KEY, "relations:deleteRelations", {"relations": relations}
    )


@app.tool()
async def get_graph() -> Any:
    return await run_convex_function(MCP_KEY, "knowledge:readGraph", {})


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
