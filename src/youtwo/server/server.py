import asyncio
import json
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

from youtwo.schemas import InitResult
from youtwo.server.config import ALLOWED_FUNCTIONS, ALLOWED_TOOLS, CONVEX_PROJECT_DIR
from youtwo.server.utils import async_convex_api_call, parse_convex_result, parse_status

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "convex@latest", "mcp", "start"],
    env=None
)

def print_tools(tools: list[Tool]):
    for tool in tools:
        print(f"Tool: {tool.name}\nDescription: {tool.description}\nInput Schema: {tool.inputSchema}\n--------------------------------")

async def list_tools():
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        await session.initialize()
        print_tools([t for t in (await session.list_tools()).tools if t.name in ALLOWED_TOOLS])

def check_convex_project(projectDir: str) -> bool:
    if not Path(projectDir).is_dir():
        print(f"Directory does not exist: {projectDir}")
        return False
    files = Path(projectDir).iterdir()
    has_pkg = "package.json" in files
    has_convex = "convex" in files and Path(projectDir, "convex").is_dir()
    print(f"Project dir: {projectDir}\nHas package.json: {has_pkg}\nHas convex/: {has_convex}")
    return has_pkg and has_convex

async def run_convex_function(deployment_selector: str, function_name: str, args: dict) -> CallToolResult:
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        try:
            await session.initialize()
            return await session.call_tool("run", {
                "deploymentSelector": deployment_selector,
                "functionName": function_name,
                "args": json.dumps(args)
            })
        except Exception as e:
            print(f"Error running function {function_name}: {e}")
            return None

async def get_function_spec(deployment_info: InitResult) -> list[dict] | None:
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        try:
            await session.initialize()
            response_dict = await session.call_tool("functionSpec", {"deploymentSelector": deployment_info["deploymentSelector"]})
            full_function_spec = json.loads(response_dict.content[0].text)
            function_spec = []
            for func in full_function_spec:
                if func.get("identifier") in ALLOWED_FUNCTIONS:
                    function_spec.append(func)
            return function_spec
        except Exception as e:
            print(f"Error getting function specs: {e}")
            return None

async def initialize_mcp(project_dir: Optional[str] = None) -> InitResult | None:
    if not project_dir:
        project_dir = CONVEX_PROJECT_DIR
    print(f"Initializing MCP with project dir: {project_dir}")
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        try:
            await session.initialize()
            deployment_info = await parse_status(await session.call_tool("status", {"projectDir": project_dir}))
            return deployment_info if deployment_info else print("No ownDev deployment found")
        except Exception as e:
            print(f"Error initializing MCP: {e}")

async def get_graph_data(deployment_info: InitResult) -> list[dict] | None:
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        try:
            await session.initialize()
            # Check for deployment info
            if not deployment_info["deploymentSelector"]:
                WIP = True
                knowledge_graph = await async_convex_api_call("graph", "GET", deployment_url=deployment_info["url"])
                with open(Path(__file__).parent / "knowledge_graph-WIP.json", "w") as f:
                    json.dump(knowledge_graph, f)
                return knowledge_graph
            res = await run_convex_function(deployment_info["deploymentSelector"], "knowledge:readGraph", {})
            return parse_convex_result(res)
        except Exception as e:
            print(f"Error getting graph data: {e}")
            return None

if __name__ == "__main__":
    deployment_info = asyncio.run(initialize_mcp())
    if deployment_info:
        list_tools()
        function_spec = asyncio.run(get_function_spec(deployment_info))
        print(function_spec)
    else:
        print("No deployment info found")
