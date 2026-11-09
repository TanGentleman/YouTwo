import json

import httpx
import pytest
from mcp import Client

from youtwo.mcp_server import make_server, site_url

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def fake_backend(requests):
    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        requests.append(
            (request.method, request.url, body, request.headers.get("authorization"))
        )
        if request.url.path.startswith("/missing"):
            return httpx.Response(404, json={"error": "nope"})
        return httpx.Response(200, json={"ok": True})

    return httpx.MockTransport(handle)


async def call(tool, args, requests, token="secret"):
    server = make_server("https://demo.convex.site", token, fake_backend(requests))
    async with Client(server) as client:
        return await client.call_tool(tool, args)


@pytest.mark.parametrize(
    ("tool", "args", "method", "path", "body"),
    [
        (
            "create_entities",
            {
                "entities": [
                    {"name": "Ada", "entityType": "person", "observations": ["x"]}
                ]
            },
            "POST",
            "/entities",
            {
                "entities": [
                    {"name": "Ada", "entityType": "person", "observations": ["x"]}
                ]
            },
        ),
        (
            "create_relations",
            {"relations": [{"from": "Ada", "to": "Acme", "relationType": "works_at"}]},
            "POST",
            "/relations",
            {"relations": [{"from": "Ada", "to": "Acme", "relationType": "works_at"}]},
        ),
        (
            "add_observations",
            {"observations": [{"entityName": "Ada", "contents": ["y"]}]},
            "POST",
            "/observations",
            {"observations": [{"entityName": "Ada", "contents": ["y"]}]},
        ),
        (
            "delete_entities",
            {"entityNames": ["Ada"]},
            "DELETE",
            "/entities",
            {"entityNames": ["Ada"]},
        ),
        (
            "delete_observations",
            {"deletions": [{"entityName": "Ada", "observations": ["y"]}]},
            "DELETE",
            "/observations",
            {"deletions": [{"entityName": "Ada", "observations": ["y"]}]},
        ),
        (
            "delete_relations",
            {"relations": [{"from": "Ada", "to": "Acme", "relationType": "works_at"}]},
            "DELETE",
            "/relations",
            {"relations": [{"from": "Ada", "to": "Acme", "relationType": "works_at"}]},
        ),
        ("read_graph", {}, "GET", "/graph", None),
    ],
)
async def test_tools_map_to_http_routes(tool, args, method, path, body):
    requests = []
    result = await call(tool, args, requests)
    assert not result.is_error
    [(sent_method, url, sent_body, auth)] = requests
    assert (sent_method, url.path, sent_body, auth) == (
        method,
        path,
        body,
        "Bearer secret",
    )


async def test_query_tools_send_query_params():
    requests = []
    await call("search_nodes", {"query": "rust"}, requests)
    await call("open_nodes", {"names": ["Ada", "Acme"]}, requests)
    assert [str(r[1]) for r in requests] == [
        "https://demo.convex.site/search?q=rust",
        "https://demo.convex.site/nodes?names=Ada%2CAcme",
    ]


async def test_http_errors_become_tool_errors():
    requests = []
    server = make_server(
        "https://demo.convex.site/missing", None, fake_backend(requests)
    )
    async with Client(server) as client:
        result = await client.call_tool("read_graph", {})
    assert result.is_error
    assert "GET /graph: 404" in result.content[0].text
    assert requests[0][3] is None


async def test_lists_the_memory_server_tools():
    server = make_server("https://demo.convex.site", None)
    async with Client(server) as client:
        tools = {t.name for t in (await client.list_tools()).tools}
    assert tools == {
        "create_entities",
        "create_relations",
        "add_observations",
        "delete_entities",
        "delete_observations",
        "delete_relations",
        "read_graph",
        "search_nodes",
        "open_nodes",
    }


def test_site_url(monkeypatch):
    monkeypatch.delenv("CONVEX_SITE_URL", raising=False)
    monkeypatch.setenv("CONVEX_URL", "https://demo.convex.cloud/")
    assert site_url() == "https://demo.convex.site"
    monkeypatch.setenv("CONVEX_SITE_URL", "http://127.0.0.1:3211/")
    assert site_url() == "http://127.0.0.1:3211"
