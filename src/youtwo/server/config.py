from pathlib import Path

CONVEX_PROJECT_DIR = Path(__file__).parent.parent.parent.parent / "backend"
ALLOWED_TOOLS = ["status", "functionSpec", "run"]

CONVEX_FUNCTION_MAP = {
    "entities.js:getBriefEntities": "Get a brief list of entities",
    "knowledge.js:readGraph": "Read the graph of the knowledge base",
    "entities.js:createEntities": "Create entities",
    "entities.js:deleteEntities": "Delete entities (by name)",
    "entities.js:addObservations": "Add observations to an entity (by name)",
    "entities.js:deleteObservations": "Delete observations from an entity (by name)",
    "relations.js:createRelations": "Create relations between entities (by name)",
    "relations.js:deleteRelations": "Delete relations between entities (by name)"
}

ALLOWED_FUNCTIONS = list(CONVEX_FUNCTION_MAP.keys())
