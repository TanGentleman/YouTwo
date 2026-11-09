# YouTwo

A knowledge-graph memory for AI agents: `youtwo-mcp` serves the [MCP memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)'s tools from a Convex database, local or cloud, instead of a JSON file.

```bash
git clone https://github.com/TanGentleman/YouTwo && cd YouTwo
uv sync --locked
cd backend && npm ci
CONVEX_AGENT_MODE=anonymous npx convex dev   # local backend on 127.0.0.1:3210, HTTP API on :3211; leave it running
```

Needs Node 22.23.4 or 26.13.0, [uv](https://docs.astral.sh/uv/) 0.13.7 and Python 3.10+; on Linux the prebuilt Convex backend needs GLIBC 2.38+. Setting a token and connecting an MCP client: [IMPLEMENTATION.md](IMPLEMENTATION.md). Roadmap: [ROADMAP.md](ROADMAP.md).

MIT licensed.
