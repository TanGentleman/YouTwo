"""Configuration settings for YouTwo server.

This module contains configuration constants for Convex functions,
allowed tools, and path definitions used throughout the YouTwo server.
"""

from pathlib import Path

from youtwo.schemas import BriefFunction

# Path Configuration
CONVEX_PROJECT_DIR = Path(__file__).parent.parent.parent.parent / "backend"
ALLOWED_TOOLS = ["status", "functionSpec", "run"]
USER_DEFAULT_MESSAGE = "Map out the characters from the TV Show "

KG_TOOLKIT: dict[str, BriefFunction] = {
    "get_entities": {
        "identifier": "entities.js:getBriefEntities",
        "description": "Get a brief list of entities",
        "tool_name": "get_entities",
    },
    "view_graph": {
        "identifier": "knowledge.js:readGraph",
        "description": "Read the graph of the knowledge base",
        "tool_name": "view_graph",
    },
    "create_entities": {
        "identifier": "entities.js:createEntities",
        "description": "Create entities",
        "tool_name": "create_entities",
    },
    "delete_entities": {
        "identifier": "entities.js:deleteEntities",
        "description": "Delete entities (by name)",
        "tool_name": "delete_entities",
    },
    "add_observations": {
        "identifier": "entities.js:addObservations",
        "description": "Add observations to an entity (by name)",
        "tool_name": "add_observations",
    },
    "delete_observations": {
        "identifier": "entities.js:deleteObservations",
        "description": "Delete observations from an entity (by name)",
        "tool_name": "delete_observations",
    },
    "create_relations": {
        "identifier": "relations.js:createRelations",
        "description": "Create relations between entities (by name)",
        "tool_name": "create_relations",
    },
    "delete_relations": {
        "identifier": "relations.js:deleteRelations",
        "description": "Delete relations between entities (by name)",
        "tool_name": "delete_relations",
    },
}

# Limitless-convex Convex Repo functions
# Source: https://github.com/TanGentleman/limitless-convex-db
MEMORIES_TOOLKIT: dict[str, dict[str, str]] = {
    "get_preview_lifelog": {
        "identifier": "dashboard/previews.js:getPreviewLifelog",
        "description": "Get the preview lifelog",
        "tool_name": "get_preview_lifelog",
    },
    "run_sync": {
        "identifier": "dashboard/sync.js:runSync",
        "description": "Run the sync",
        "tool_name": "run_sync",
    },
    "list_schedules": {
        "identifier": "extras/schedules.js:listSchedules",
        "description": "List the schedules",
        "tool_name": "list_schedules",
    },
    "schedule_sync": {
        "identifier": "extras/schedules.js:scheduleSync",
        "description": "Schedule the sync",
        "tool_name": "schedule_sync",
    },
    "undo_sync": {
        "identifier": "extras/tests.js:undoSync",
        "description": "Undo the last sync",
        "tool_name": "undo_sync",
    },
    "get_metadata_doc": {
        "identifier": "extras/tests.js:getMetadataDoc",
        "description": "Get the metadata doc",
        "tool_name": "get_metadata_doc",
    },
    "paginated_docs": {
        "identifier": "lifelogs.js:paginatedDocs",
        "description": "Paginate through the lifelogs",
        "tool_name": "paginated_docs",
    },
    "search_markdown": {
        "identifier": "lifelogs.js:searchMarkdown",
        "description": "Search the markdown",
        "tool_name": "search_markdown",
    },
}

KG_BY_IDENTIFIER: dict[str, BriefFunction] = {
    val["identifier"]: val for val in KG_TOOLKIT.values()
}

MEMORIES_BY_IDENTIFIER: dict[str, BriefFunction] = {
    val["identifier"]: val for val in MEMORIES_TOOLKIT.values()
}

# Derived constants
ALLOWED_FUNCTIONS: list[str] = list(KG_TOOLKIT.keys())
