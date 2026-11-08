# YouTwo: implementation

## Requirements

- Node 22.23.4 or 26.13.0, [uv](https://docs.astral.sh/uv/) 0.13.7 and Python 3.10+.
- The prebuilt Convex backend needs GLIBC 2.38 or newer on Linux. `npx convex dev` downloads it on first
  use.
- A Convex account only for a cloud deployment; the local anonymous backend needs none.

## Usage

### Local backend and token

Start the backend as in the README (`CONVEX_AGENT_MODE=anonymous npx convex dev` in `backend/`, left
running), then in a second terminal:

```bash
cd YouTwo/backend
CONVEX_AGENT_MODE=anonymous npx convex env set YOUTWO_API_TOKEN "$(openssl rand -hex 16)"
CONVEX_AGENT_MODE=anonymous npx convex env get YOUTWO_API_TOKEN
```

### MCP client

Add the server to your MCP client. For Claude Desktop:

```json
{
  "mcpServers": {
    "youtwo": {
      "command": "uv",
      "args": ["--directory", "/path/to/YouTwo", "run", "youtwo-mcp"],
      "env": { "CONVEX_SITE_URL": "http://127.0.0.1:3211", "YOUTWO_API_TOKEN": "<token>" }
    }
  }
}
```

For a Convex cloud deployment, run `npx convex dev` without `CONVEX_AGENT_MODE` (it asks you to log in
and pick a deployment), set the token the same way, and use `"CONVEX_URL": "https://<name>.convex.cloud"`
instead of `CONVEX_SITE_URL`.

### MCP server environment

`youtwo-mcp` also reads these from `.env` in the repo root.

| Variable | Meaning |
| --- | --- |
| `CONVEX_URL` | `https://<name>.convex.cloud`; the HTTP API is on the matching `.convex.site` |
| `CONVEX_SITE_URL` | the HTTP API base itself, e.g. `http://127.0.0.1:3211`; wins over `CONVEX_URL` |
| `YOUTWO_API_TOKEN` | the bearer token set on the deployment |

A failed HTTP call comes back to the client as a tool error carrying the status and body, e.g.
`GET /graph: 401 {"error":"unauthorized"}`.

### HTTP API

`backend/convex/http.ts`. Every route needs `Authorization: Bearer $YOUTWO_API_TOKEN`.

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

| Status | When |
| --- | --- |
| 200 | success |
| 400 | malformed body or missing query parameter |
| 401 | missing or wrong token |
| 500 | `YOUTWO_API_TOKEN` is not set on the deployment |

```bash
curl -H "Authorization: Bearer $YOUTWO_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"entities": [{"name": "Ada", "entityType": "person", "observations": ["Writes Rust"]}]}' \
  http://127.0.0.1:3211/entities
```

## How it works

- `backend/convex/`: `schema.ts`, `entities.ts`, `relations.ts`, `knowledge.ts` (graph queries) and
  `http.ts` (the routes above, each checking the bearer token), plus the tests. `convex/_generated` is
  committed.
- `src/youtwo/mcp_server.py`: the stdio MCP server, a thin client of the HTTP API. Its tools are the
  memory server's: `create_entities`, `create_relations`, `add_observations`, `delete_entities`,
  `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`, `open_nodes`.

## Tests

Offline; no backend or deployment needed. CI (`.github/workflows/ci.yml`) runs the backend job on Node
22.23.4 and 26.13.0 and the Python job on Python 3.10.22 and 3.14.10:

```bash
cd backend && npm ci && npm run typecheck && npm test   # convex-test, in memory
cd .. && uv sync --locked && uv run pytest              # MCP server against a fake HTTP backend
```

## Limits

- `youtwo-mcp` talks only to the configured Convex site URL.
- Checked against a local anonymous backend only: every MCP tool over stdio, and a wrong token giving a
  401 tool error. No Convex cloud deployment and no real MCP client (such as Claude Desktop) were tried.
