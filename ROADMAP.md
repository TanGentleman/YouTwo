# YouTwo roadmap

YouTwo is a memory layer for AI agents: a Convex backend that stores a knowledge graph of entities
(people, organizations, ...), the relations between them and observations (atomic facts) about them,
exposed over HTTP and as MCP tools. It's for someone who wants an agent like Claude Desktop or a
smolagents agent to remember who's who across conversations. The repo also holds a June 2025
hackathon demo: a Gradio chat app that does Vectara RAG and draws the graph.

## Status at upstream 703927e (checked 2026-11-08)

| Claim | Evidence |
| --- | --- |
| Backend installs, typechecks and deploys on convex 1.49 | `npm install`, `npx tsc --noEmit -p convex`, `CONVEX_AGENT_MODE=anonymous npx convex dev --once` (local backend, no account) |
| Its built-in test action passes 9/9 | `npx convex run tests:runTests` against the local backend |
| HTTP API works, with no auth on any route (including DELETE) | curl of every route in `http.ts` against `127.0.0.1:3211` |
| `delete_observations` (MCP and agent tool) always failed | sends `{entityName, contents}`; Convex wants `deletions: [{entityName, observations}]`; HTTP 500. Fixed on `-1` |
| `scripts/run_gradio_app.py` didn't start | `No module named 'src'`, then gradio 6 `TypeError: show_download_button`. Fixed on `-1` |
| `scripts/run_mcp.py` needs a logged-in Convex CLI | it drives `npx convex mcp start`; with a local anonymous backend `status` returns `Not Authorized` |
| `deployment/modal_app.py` can't build | adds `src/yt_rag/rag.py`, `src/yt_gradio/app.py`, ... which don't exist |
| Dead links | the Modal app in the README returns 404; the repo homepage (you-two-delta.vercel.app) serves the stock Docusaurus template |
| Dependencies were unpinned | `.gitignore` ignored `uv.lock`, `package-lock.json` and every `*.json`. Lockfiles committed on `-1` |
| Python imports | every module imports after `uv sync --all-extras`; `agents.agent` and `frontend.app` need `NEBIUS_API_KEY` set at import |
| Lint | `uvx ruff check src scripts`: 128 findings with the repo's own config (not fixed) |

## Signal vs noise

Keep: `backend/convex` entities, relations, observations and the graph queries (`entities.ts`,
`relations.ts`, `knowledge.ts`, `schema.ts`, `http.ts`), and a thin Python MCP server that calls
the HTTP API.

Cut on `YouTwo-3`: `project-website/` (Docusaurus template: 2019/2021 sample posts, undraw images, `url:
'https://example.com'`), `examples/*.ipynb`, `plan.md` (hackathon brainstorm), `requirements*.txt`
(duplicate `pyproject.toml`), `scripts/alert_mcp.py` and `scripts/limitless_mcp.py` (servers for
other projects; `/ping` isn't in this backend), `backend/convex/embeddings.ts` (random mock
vectors), `patches.ts` (one-off migration), the broken Modal
deploy. Cut on `YouTwo-6`: the Vectara RAG, Gradio app, smolagents and langgraph code. Cut on
`YouTwo-7`: the journals/sources/metadata tables that only the Vectara sync used.

## Stack

Each branch is based on the one before it in TanGentleman/kranti-sandbox.

- `YouTwo-1` (done): import, this roadmap, lockfiles, `delete_observations` and `check_convex_project` fixes, Gradio app starts again, README setup fixes.
- `YouTwo-2` (done): convex-test unit tests (`cd backend && npm test`) replace `tests:runTests`; pytest for the Python fixes; committed `convex/_generated`; GitHub Actions CI (`.github/workflows/ci.yml`, runs once applied upstream).
- `YouTwo-3` (done): cut the noise listed above (website, notebooks, plan, requirements files, other projects' MCP scripts, `embeddings.ts`, `patches.ts`, the Modal deploy): 108 files to 61.
- `YouTwo-4` (done): bearer-token auth (`YOUTWO_API_TOKEN`) on every HTTP route, Python clients send it; fix the RAG sync calling a missing `/metadata` route.
- `YouTwo-5` (done): `youtwo-mcp`, a stdio MCP server over the HTTP API with the reference memory server's tools, tested offline and against a local backend; replaces `scripts/run_mcp*.py`.
- `YouTwo-6` (done): cut the Python side to `youtwo-mcp` (drop the Gradio/Vectara/smolagents/langgraph demo; deps down to httpx, mcp, python-dotenv; mcp 1.10 to 1.30); README rewritten around the MCP server.
- `YouTwo-7` (done): drop the journals/sources/metadata tables, the `/sources` routes and uncalled internal functions; old documents still validate (tested by pushing over a local backend with rows in every old table).
- `YouTwo-8` (done): mcp 1.30 to 2.3.0 (`FastMCP` is now `MCPServer`; HTTP errors raise `ToolError` so the status still reaches the client; tests use `mcp.Client`); `typing_extensions.TypedDict`, which pydantic needs on Python < 3.12; every dependency pinned exactly; CI on actions v7 and setup-uv v10.3.3 with Node 22.23.4/26.13.0 and Python 3.10.22/3.14.10; README quickstart on a local anonymous backend; the boilerplate `backend/README.md` removed.
- `YouTwo-9`: README cut to 91 words; details moved to IMPLEMENTATION.md.

## Applying the stack upstream

The import commit is `8358445`. In a clean upstream checkout at 703927e, next to `kranti-sandbox`:

```bash
git -C ../kranti-sandbox fetch origin
git -C ../kranti-sandbox format-patch --relative=YouTwo -o /tmp/youtwo 8358445..origin/YouTwo-9
git am /tmp/youtwo/*.patch
```

To stop at an earlier branch, use `8358445..origin/YouTwo-<n>`. No `--keep-cr` needed. Checked on
fresh clones at `-9`: the result matches `origin/YouTwo-9:YouTwo`, and the Tests commands in
IMPLEMENTATION.md pass.

## Needs Tan

- `YouTwo-4` changes the API: after applying it, run `npx convex env set YOUTWO_API_TOKEN <token>` on the deployment and put the same token in `.env`, or every route returns 500.
- `YouTwo-7` changes the schema. Convex keeps the rows of the dropped tables; clear them in the dashboard if wanted. `journalIds` stays as an optional unused field so existing entities validate; removing it needs a migration.
- Not verified: a Convex cloud deployment, a real MCP client such as Claude Desktop, and (before `-6`) anything needing Vectara, Nebius or Modal keys.
- CI has not run on GitHub; it runs once the stack is applied upstream.
- `YouTwo-3` deletes the Modal deploy instead of fixing it, since a fix can't be tested without a Modal account. `YouTwo-6` goes further and treats the knowledge-graph MCP server as the product, deleting the Gradio/RAG demo. Stop at `-5` to keep the demo.
- The GitHub repo homepage points at the Docusaurus template site; change or clear it in the repo settings.
