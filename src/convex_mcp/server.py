import json
from pathlib import Path
from pprint import pprint
from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult
from src.convex_mcp.config import InitResult, CONVEX_PROJECT_DIR, ALLOWED_TOOLS
import asyncio

from src.convex_mcp.utils import parse_status

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
            result = await session.call_tool("run", {
                "deploymentSelector": deployment_selector,
                "functionName": function_name,
                "args": json.dumps(args)
            })
            return result
        except Exception as e:
            print(f"Error running function {function_name}: {e}")
            return None

async def initialize_mcp(project_dir: str = CONVEX_PROJECT_DIR) -> InitResult | None:
    print(f"Initializing MCP with project dir: {project_dir}")
    if not check_convex_project(project_dir):
        print("Invalid Convex project directory")
        return
    async with stdio_client(server_params) as (read, write), \
         ClientSession(read, write) as session:
        try:
            await session.initialize()
            deployment_info = await parse_status(await session.call_tool("status", {"projectDir": project_dir}))
            return deployment_info if deployment_info else print("No ownDev deployment found")
        except Exception as e:
            print(f"Error initializing MCP: {e}")

if __name__ == "__main__":
    deployment_info = asyncio.run(initialize_mcp())
    if deployment_info:
        list_tools()
    else:
        print("No deployment info found")
