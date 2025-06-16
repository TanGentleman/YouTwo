import asyncio
import logging
import json
from pathlib import Path
from pprint import pprint
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.convex_mcp.utils import parse_convex_result

server_params = StdioServerParameters(
    command="uv",
    args=["--directory", f"{Path(__file__).parent.resolve()}", "run", "run_mcp.py"],
    env=None
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    async with stdio_client(server_params) as (read, write), \
             ClientSession(read, write) as session:
        await session.initialize()
        return await session.call_tool("create_entities", {"entities": [{"name": "CMU", "entityType": "university"}]})

if __name__ == "__main__":
    res = asyncio.run(main())
    res = parse_convex_result(res)
    pprint(res)