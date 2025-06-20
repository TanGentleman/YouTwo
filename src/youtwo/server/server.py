import asyncio
import json
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client

from youtwo.exceptions import ToolCallError
from youtwo.schemas import BriefFunction, ConvexFunctionSpec, InitResult
from youtwo.server.config import ALLOWED_TOOLS, CONVEX_PROJECT_DIR, KG_BY_IDENTIFIER
from youtwo.server.utils import async_convex_api_call, dictify_tool_call, parse_status

server_params = StdioServerParameters(
    command="npx", args=["-y", "convex@latest", "mcp", "start"], env=None
)


def print_tool_info(tools: list[Tool]):
    for tool in tools:
        print(
            f"Tool: {tool.name}\nDescription: {tool.description}\nInput Schema: {tool.inputSchema}\n--------------------------------"
        )


async def print_tools() -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = [
            t for t in (await session.list_tools()).tools if t.name in ALLOWED_TOOLS
        ]
        print_tool_info(tools)


def check_convex_project(project_dir: str) -> bool:
    if not Path(project_dir).is_dir():
        print(f"Directory does not exist: {project_dir}")
        return False
    files = Path(project_dir).iterdir()
    has_pkg = "package.json" in files
    has_convex = "convex" in files and Path(project_dir, "convex").is_dir()
    print(
        f"Project dir: {project_dir}\nHas package.json: {has_pkg}\nHas convex/: {has_convex}"
    )
    return has_pkg and has_convex


async def run_convex_function(
    deployment_selector: str, function_name: str, args: dict
) -> dict | None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        try:
            await session.initialize()
            result_object = await session.call_tool(
                "run",
                {
                    "deploymentSelector": deployment_selector,
                    "functionName": function_name,
                    "args": json.dumps(args),
                },
            )
            # dictify may raise ToolCallError
            res = dictify_tool_call(result_object)
            return res["result"]
        except ToolCallError as e:
            print(f"Tool call error: {e}")
            raise e
        except Exception as e:
            print(f"Error running function {function_name}: {e}")
            raise e


async def get_function_spec(
    deployment_info: InitResult,
    allowed_function_map: dict[str, BriefFunction] = KG_BY_IDENTIFIER,
) -> list[ConvexFunctionSpec] | None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        try:
            await session.initialize()
            response_dict = await session.call_tool(
                "functionSpec",
                {"deploymentSelector": deployment_info["deploymentSelector"]},
            )
            full_function_spec = dictify_tool_call(response_dict)
            function_spec = []
            for func in full_function_spec:
                val = allowed_function_map.get(func.get("identifier"))
                if val:
                    tool_dict = {
                        "identifier": func["identifier"],
                        "function_args": func["args"],
                        "tool_name": val["tool_name"],
                        "description": val["description"],
                    }
                    function_spec.append(tool_dict)
            return function_spec
        except Exception as e:
            print(f"Error getting function specs: {e}")
            return None


async def initialize_mcp(project_dir: Optional[str] = None) -> InitResult | None:
    if not project_dir:
        project_dir = CONVEX_PROJECT_DIR
    print(f"Initializing MCP with project dir: {project_dir}")
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        try:
            await session.initialize()
            deployment_info = await parse_status(
                await session.call_tool("status", {"projectDir": project_dir})
            )
            return (
                deployment_info
                if deployment_info
                else print("No ownDev deployment found")
            )
        except Exception as e:
            print(f"Error initializing MCP: {e}")


async def get_graph_data(deployment_info: InitResult) -> list[dict] | None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        try:
            await session.initialize()
            # Check for deployment info
            if not deployment_info["deploymentSelector"]:
                knowledge_graph = await async_convex_api_call(
                    "graph", "GET", deployment_url=deployment_info["url"]
                )
                with open(Path(__file__).parent / "knowledge_graph-WIP.json", "w") as f:
                    json.dump(knowledge_graph, f)
                return knowledge_graph
            return await run_convex_function(
                deployment_info["deploymentSelector"], "knowledge:readGraph", {}
            )
        except Exception as e:
            print(f"Error getting graph data: {e}")
            return None


async def main():
    deployment_info = await initialize_mcp()
    if deployment_info:
        await print_tools()
        function_spec = await get_function_spec(deployment_info)
        print([func["identifier"] for func in function_spec])
        # await get_graph_data(deployment_info)
    else:
        print("No deployment info found")


if __name__ == "__main__":
    asyncio.run(main())
