# YouTwo

A knowledge-graph memory for AI agents. A [Convex](https://convex.dev) backend stores entities
(people, organizations, places), relations between them and observations (facts) about them.
`youtwo-mcp` serves the graph over MCP with the same tools as the reference
[memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory), so the graph
lives in a database instead of a local JSON file.

## Quickstart (local backend, no account)

Needs Node 22.23.4 or 26.13.0, [uv](https://docs.astral.sh/uv/) 0.13.7 and Python 3.10+. The
prebuilt Convex backend needs GLIBC 2.38 or newer on Linux.

```bash
git clone https://github.com/TanGentleman/YouTwo && cd YouTwo
cd backend && npm ci
CONVEX_AGENT_MODE=anonymous npx convex dev   # local backend on 127.0.0.1:3210, HTTP API on :3211; leave it running
```

In a second terminal:

```bash
cd YouTwo/backend
CONVEX_AGENT_MODE=anonymous npx convex env set YOUTWO_API_TOKEN "$(openssl rand -hex 16)"
CONVEX_AGENT_MODE=anonymous npx convex env get YOUTWO_API_TOKEN
cd .. && uv sync --locked
```

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

For a Convex cloud deployment, run `npx convex dev` without `CONVEX_AGENT_MODE` (it asks you to log
in and pick a deployment), set the token the same way, and use
`"CONVEX_URL": "https://<name>.convex.cloud"` instead of `CONVEX_SITE_URL`.

## MCP server environment

`youtwo-mcp` also reads these from `.env` in the repo root.

| Variable | Meaning |
| --- | --- |
| `CONVEX_URL` | `https://<name>.convex.cloud`; the HTTP API is on the matching `.convex.site` |
| `CONVEX_SITE_URL` | the HTTP API base itself, e.g. `http://127.0.0.1:3211`; wins over `CONVEX_URL` |
| `YOUTWO_API_TOKEN` | the bearer token set on the deployment |

A failed HTTP call comes back to the client as a tool error carrying the status and body, e.g.
`GET /graph: 401 {"error":"unauthorized"}`.

## HTTP API

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

## Tests

Offline; no backend or deployment needed. CI runs the same commands.

```bash
cd backend && npm ci && npm run typecheck && npm test   # convex-test, in memory
cd .. && uv sync --locked && uv run pytest              # MCP server against a fake HTTP backend
```

## Layout

- `backend/convex/`: `schema.ts`, `entities.ts`, `relations.ts`, `knowledge.ts` (graph queries),
  `http.ts`, and the tests. `convex/_generated` is committed.
- `src/youtwo/mcp_server.py`: the MCP server, a thin client of the HTTP API.

## Boundaries

- `youtwo-mcp` talks only to the configured Convex site URL. `npx convex dev` downloads the
  backend binary on first use; a cloud deployment needs a Convex account.
- Checked against a local anonymous backend only: every MCP tool over stdio, and a wrong token
  giving a 401 tool error. No Convex cloud deployment and no real MCP client (such as Claude
  Desktop) were tried.

## License

MIT
