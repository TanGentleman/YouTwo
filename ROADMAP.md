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
deploy. Cut on `YouTwo-6`: the Vectara RAG, Gradio app, smolagents and langgraph code. Still in
the backend: the journals/sources/metadata tables that only the Vectara sync used.

## Stack

Each branch is based on the one before it in TanGentleman/kranti-sandbox.

- `YouTwo-1` (done): import, this roadmap, lockfiles, `delete_observations` and `check_convex_project` fixes, Gradio app starts again, README setup fixes.
- `YouTwo-2` (done): convex-test unit tests (`cd backend && npm test`) replace `tests:runTests`; pytest for the Python fixes; committed `convex/_generated`; GitHub Actions CI (`.github/workflows/ci.yml`, runs once applied upstream).
- `YouTwo-3` (done): cut the noise listed above (website, notebooks, plan, requirements files, other projects' MCP scripts, `embeddings.ts`, `patches.ts`, the Modal deploy): 95 files to 61.
- `YouTwo-4` (done): bearer-token auth (`YOUTWO_API_TOKEN`) on every HTTP route, Python clients send it; fix the RAG sync calling a missing `/metadata` route.
- `YouTwo-5` (done): `youtwo-mcp`, a stdio MCP server over the HTTP API with the reference memory server's tools, tested offline and against a local backend; replaces `scripts/run_mcp*.py`.
- `YouTwo-6` (done): cut the Python side to `youtwo-mcp` (drop the Gradio/Vectara/smolagents/langgraph demo; deps down to httpx, mcp, python-dotenv; mcp 1.10 to 1.30); README rewritten around the MCP server.

## Applying a branch upstream

From a clean upstream checkout at 703927e, for branch `YouTwo-N`. The base of `YouTwo-1` is the
import commit, `8358445`; the base of `YouTwo-N` is `YouTwo-<N-1>`. Apply the branches in order.

```bash
git -C ../kranti-sandbox fetch origin
git -C ../kranti-sandbox format-patch --relative=YouTwo -o /tmp/youtwo-N origin/YouTwo-<N-1>..origin/YouTwo-N
git am /tmp/youtwo-N/*.patch
```

## Needs Tan

- `YouTwo-1` pins `gradio[mcp]<6` instead of porting the app to gradio 6 (that pin holds `mcp` at 1.10.1). `YouTwo-6` drops gradio and pins `mcp>=1.10,<2`; mcp 2.x changes the server API.
- `YouTwo-4` changes the API: after applying it, run `npx convex env set YOUTWO_API_TOKEN <token>` on the deployment and put the same token in `.env`, or every route returns 500.
- Not verified: anything needing Vectara, Nebius or Modal keys (RAG answers, agent runs, deploys) or a Convex cloud deployment.
- `YouTwo-3` deletes the Modal deploy instead of fixing it, since a fix can't be tested without a Modal account. `YouTwo-6` goes further and treats the knowledge-graph MCP server as the product, deleting the Gradio/RAG demo. Stop at `-5` to keep the demo.
- The GitHub repo homepage points at the Docusaurus template site; change or clear it in the repo settings.
