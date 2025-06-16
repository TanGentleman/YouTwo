from src.schemas import ConvexCreateEntity, ConvexCreateRelation
from src.convex_mcp.server import run_convex_function
from src.schemas import InitResult
from mcp.types import CallToolResult

async def create_entities(deployment_info: InitResult, entities: list[ConvexCreateEntity]) -> CallToolResult:
    deployment_selector = deployment_info["deploymentSelector"]
    function_name = "entities:createEntities"
    function_args = {
        "entities": entities
    }
    return await run_convex_function(deployment_selector, function_name, function_args)

async def create_relations(deployment_info: InitResult, relations: list[ConvexCreateRelation]) -> CallToolResult:
    deployment_selector = deployment_info["deploymentSelector"]
    function_name = "relations:createRelations"
    function_args = {
        "relations": relations
    }
    return await run_convex_function(deployment_selector, function_name, function_args)


async def get_graph(deployment_info: InitResult) -> CallToolResult:
    deployment_selector = deployment_info["deploymentSelector"]
    function_name = "knowledge:readGraph"
    function_args = {}
    return await run_convex_function(deployment_selector, function_name, function_args)