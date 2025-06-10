# YouTwo Memory

Our gradio app for MCP-powered memory.

# YouTwo Knowledge Graph Memory Server

A full RAG pipeline using Vectara, with an optional persistent memory system using a knowledge graph, built with Convex backend. This system allows for storing information about entities, their relations, and observations across multiple interactions.

# This app is deployed on the current link: <>

# Run this app locally
```bash
git clone https://github.com/TanGentleman/YouTwo
cd YouTwo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_gradio_app.py
```

# Deploy the server
```bash
cd YouTwo
modal deploy run_modal_app.py
```

## Overview

The knowledge graph memory server implements:

1. **Entity Management**: Create, update, and delete entities with associated metadata
2. **Relationship Tracking**: Track how entities relate to each other
3. **Journal System**: Record timestamped entries that can be analyzed for entity extraction
4. **Semantic Search**: Find semantically similar content using vector embeddings
5. **HTTP API**: External integration with the knowledge graph

## Setup Instructions

### Prerequisites

- Node.js (v14 or later)
- npm

### Installation

1. Clone the repository:
```bash
git clone https://github.com/TanGentleman/YouTwo
cd YouTwo/backend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server (You will be prompted to login to Convex):
```bash
npx convex dev
```

Expose all our backend functions easily using MCP or even http requests. See:
https://docs.convex.dev/client/react/deployment-urls
https://docs.convex.dev/ai/convex-mcp-server

## API Usage

The system provides both a JavaScript API and HTTP endpoints for managing the knowledge graph.

### JavaScript API

#### Creating Entities

```javascript
await createEntities({
  entities: [
    {
      name: "John_Smith",
      entityType: "person",
      observations: ["Speaks fluent Spanish", "Graduated in 2019"]
    }
  ]
});
```

#### Creating Relations

```javascript
await createRelations({
  relations: [
    {
      from: "John_Smith",
      to: "Anthropic",
      relationType: "works_at"
    }
  ]
});
```

#### Reading the Graph

```javascript
const graph = await readGraph();
```

#### Searching Nodes

```javascript
const results = await searchNodes({ query: "Spanish speaker" });
```

### HTTP API

The system also exposes HTTP endpoints for external integration:

- `POST /entities` - Create entities
- `POST /relations` - Create relations
- `POST /observations` - Add observations to entities
- `GET /graph` - Read the entire knowledge graph
- `GET /search?q=query` - Search nodes by query
- `GET /nodes?names=name1,name2` - Get specific nodes by name
- `DELETE /entities` - Delete entities
- `DELETE /observations` - Delete observations
- `DELETE /relations` - Delete relations

## Architecture

The system is built using Convex for the backend database and API. The codebase is structured as follows:

- `backend/convex/` - Convex backend code
  - `schema.ts` - Database schema definition
  - `entities.ts` - Entity management functions
  - `relations.ts` - Relation management functions
  - `knowledge.ts` - Knowledge graph query functions
  - `journals.ts` - Journal entry management
  - `embeddings.ts` - Vector embedding functions
  - `distiller.ts` - Knowledge extraction from journals
  - `operations.ts` - Operation logging utilities
  - `http.ts` - HTTP API endpoints

## License

MIT