"""MCP server for the YouTwo knowledge graph.

A thin stdio MCP server over the Convex HTTP API in backend/convex/http.ts. Tool
names and arguments follow the reference MCP memory server
(@modelcontextprotocol/server-memory), so clients written for it work unchanged.

Environment:
    CONVEX_URL        https://<name>.convex.cloud (the HTTP API is on .convex.site)
    CONVEX_SITE_URL   optional; the HTTP API base itself, e.g. http://127.0.0.1:3211
    YOUTWO_API_TOKEN  bearer token set on the deployment
"""

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from typing_extensions import TypedDict


class Entity(TypedDict, total=False):
    name: str
    entityType: str
    observations: list[str]


Relation = TypedDict("Relation", {"from": str, "to": str, "relationType": str})


class NewObservations(TypedDict):
    entityName: str
    contents: list[str]


class ObservationDeletion(TypedDict):
    entityName: str
    observations: list[str]


def site_url() -> str:
    if url := os.getenv("CONVEX_SITE_URL"):
        return url.rstrip("/")
    url = os.getenv("CONVEX_URL")
    if not url:
        raise RuntimeError("Set CONVEX_URL (or CONVEX_SITE_URL)")
    return url.replace(".convex.cloud", ".convex.site").rstrip("/")


def make_server(  # noqa: C901 (one nested function per tool)
    base_url: str, token: str | None, transport: httpx.AsyncBaseTransport | None = None
) -> MCPServer:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    mcp = MCPServer("youtwo", log_level="WARNING")

    async def call(method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(
            base_url=base_url, headers=headers, transport=transport, timeout=20
        ) as client:
            response = await client.request(method, path, **kwargs)
        if response.is_error:
            raise ToolError(
                f"{method} {path}: {response.status_code} {response.text}"
            )
        return response.json()

    @mcp.tool()
    async def create_entities(entities: list[Entity]) -> Any:
        """Create entities. Names are unique; existing names are reported, not changed."""
        return await call("POST", "/entities", json={"entities": entities})

    @mcp.tool()
    async def create_relations(relations: list[Relation]) -> Any:
        """Create relations between existing entities. Use active voice for relationType."""
        return await call("POST", "/relations", json={"relations": relations})

    @mcp.tool()
    async def add_observations(observations: list[NewObservations]) -> Any:
        """Add facts (observations) to existing entities."""
        return await call("POST", "/observations", json={"observations": observations})

    @mcp.tool()
    async def delete_entities(entityNames: list[str]) -> Any:  # noqa: N803
        """Delete entities and their relations."""
        return await call("DELETE", "/entities", json={"entityNames": entityNames})

    @mcp.tool()
    async def delete_observations(deletions: list[ObservationDeletion]) -> Any:
        """Delete specific observations from entities."""
        return await call("DELETE", "/observations", json={"deletions": deletions})

    @mcp.tool()
    async def delete_relations(relations: list[Relation]) -> Any:
        """Delete relations."""
        return await call("DELETE", "/relations", json={"relations": relations})

    @mcp.tool()
    async def read_graph() -> Any:
        """Read the whole knowledge graph."""
        return await call("GET", "/graph")

    @mcp.tool()
    async def search_nodes(query: str) -> Any:
        """Find entities whose name, type or observations contain the query."""
        return await call("GET", "/search", params={"q": query})

    @mcp.tool()
    async def open_nodes(names: list[str]) -> Any:
        """Get entities by name, with the relations that touch them."""
        return await call("GET", "/nodes", params={"names": ",".join(names)})

    return mcp


def main() -> None:
    load_dotenv()
    make_server(site_url(), os.getenv("YOUTWO_API_TOKEN")).run()


if __name__ == "__main__":
    main()
