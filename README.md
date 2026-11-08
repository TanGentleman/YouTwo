# YouTwo

Memory for AI agents. YouTwo stores a knowledge graph of entities (people, organizations,
places), the relations between them, and observations (facts) about them in a
[Convex](https://convex.dev) backend, and serves it to agents as an MCP server. The MCP tools
match the reference [memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory),
so the graph persists across conversations and machines instead of living in a local JSON file.

## Run it

Needs Node 22+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/TanGentleman/YouTwo && cd YouTwo
cd backend && npm ci
npx convex dev                     # pick a deployment; leave it running
npx convex env set YOUTWO_API_TOKEN "$(openssl rand -hex 16)"
cd .. && uv sync
```

Then add the server to your MCP client. For Claude Desktop:

```json
{
  "mcpServers": {
    "youtwo": {
      "command": "uv",
      "args": ["--directory", "/path/to/YouTwo", "run", "youtwo-mcp"],
      "env": { "CONVEX_URL": "https://<name>.convex.cloud", "YOUTWO_API_TOKEN": "<token>" }
    }
  }
}
```

`npx convex env get YOUTWO_API_TOKEN` prints the token. Against a local backend, set
`CONVEX_SITE_URL=http://127.0.0.1:3211` instead of `CONVEX_URL`.

## HTTP API

`backend/convex/http.ts`. Every route needs `Authorization: Bearer $YOUTWO_API_TOKEN`; with the
token unset on the deployment, every route returns 500.

| Route | Body or query |
| --- | --- |
| `POST /entities` | `{"entities": [{"name", "entityType", "observations"?}]}` |
| `POST /relations` | `{"relations": [{"from", "to", "relationType"}]}` |
| `POST /observations` | `{"observations": [{"entityName", "contents"}]}` |
| `DELETE /entities` | `{"entityNames": [...]}` (also deletes their relations) |
| `DELETE /relations` | `{"relations": [{"from", "to", "relationType"}]}` |
| `DELETE /observations` | `{"deletions": [{"entityName", "observations"}]}` |
| `GET /graph` | the whole graph |
| `GET /entities` | names and types |
| `GET /search?q=` | entities whose name, type or observations contain `q` |
| `GET /nodes?names=a,b` | the named entities and their relations |

```bash
curl -H "Authorization: Bearer $YOUTWO_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"entities": [{"name": "Ada", "entityType": "person", "observations": ["Writes Rust"]}]}' \
  https://<name>.convex.site/entities
```

## Layout

- `backend/convex/`: schema, `entities.ts`, `relations.ts`, `knowledge.ts` (graph queries),
  `http.ts`, and convex-test unit tests.
- `src/youtwo/mcp_server.py`: the MCP server, a thin client of the HTTP API.

## Test

```bash
cd backend && npm run typecheck && npm test   # in memory, no deployment
uv run pytest                                 # MCP server against a fake HTTP backend
```

## License

MIT
