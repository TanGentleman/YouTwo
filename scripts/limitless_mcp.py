import asyncio
import logging
from typing import Any, Optional
from pathlib import Path

from mcp import types
from mcp.server.fastmcp import FastMCP

from youtwo.server.server import get_function_spec, initialize_mcp, run_convex_function
from youtwo.server.config import MEMORIES_BY_IDENTIFIER

# Configuration for Limitless Convex database directory
LIMITLESS_MCP_DIR = Path("~/Documents/GitHub/fresh-limitless-convex-db/convex-app")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("Limitless MCP")
deployment_info = asyncio.run(initialize_mcp(str(LIMITLESS_MCP_DIR.expanduser())))
if not deployment_info:
    print("No deployment found")
    exit(1)

MCP_KEY = deployment_info["deploymentSelector"]

@app.tool()
async def get_preview_lifelog() -> Any:
    """
    Get the preview lifelog.
    """
    return await run_convex_function(MCP_KEY, "dashboard/previews:getPreviewLifelog", {})


@app.tool()
async def run_sync(send_notification: Optional[bool] = None) -> Any:
    """
    Run the sync.
    
    Args:
        send_notification: Optional boolean to send notification after sync
    """
    params = {}
    if send_notification is not None:
        params["sendNotification"] = send_notification
    return await run_convex_function(MCP_KEY, "dashboard/sync:runSync", params)


@app.tool()
async def list_schedules(limit: Optional[int] = None) -> Any:
    """
    List the schedules.
    
    Args:
        limit: Optional limit on number of schedules to return
    """
    params = {}
    if limit is not None:
        params["limit"] = limit
    return await run_convex_function(MCP_KEY, "extras/schedules:listSchedules", params)


@app.tool()
async def schedule_sync(
    days: Optional[int] = None,
    hours: Optional[int] = None, 
    minutes: Optional[int] = None,
    seconds: Optional[int] = None
) -> Any:
    """
    Schedule the sync.
    
    Args:
        days: Optional number of days for schedule
        hours: Optional number of hours for schedule
        minutes: Optional number of minutes for schedule
        seconds: Optional number of seconds for schedule
    """
    params = {}
    if days is not None:
        params["days"] = days
    if hours is not None:
        params["hours"] = hours
    if minutes is not None:
        params["minutes"] = minutes
    if seconds is not None:
        params["seconds"] = seconds
    return await run_convex_function(MCP_KEY, "extras/schedules:scheduleSync", params)


@app.tool()
async def undo_sync(dry_run: Optional[bool] = None) -> Any:
    """
    Undo the last sync.
    
    Args:
        dry_run: Optional boolean to run in dry-run mode
    """
    params = {}
    if dry_run is not None:
        params["dryRun"] = dry_run
    return await run_convex_function(MCP_KEY, "extras/tests:undoSync", params)


@app.tool()
async def get_metadata_doc() -> Any:
    """
    Get the metadata doc.
    """
    return await run_convex_function(MCP_KEY, "extras/tests:getMetadataDoc", {})


class PaginationOpts:
    def __init__(
        self,
        cursor: Optional[str],
        num_items: int,
    ):
        self.cursor = cursor
        self.num_items = num_items
    
    def to_dict(self):
        result = {
            "cursor": self.cursor,
            "numItems": self.num_items
        }
        return result


@app.tool()
async def paginated_docs(
    cursor: Optional[str],
    num_items: int,
    direction: Optional[str] = None,
    end_time: Optional[int] = None,
    start_time: Optional[int] = None,
) -> Any:
    """
    Paginate through the lifelogs.
    
    Args:
        cursor: Cursor for pagination (required)
        num_items: Number of items to return (required)
        direction: Optional direction ('asc' or 'desc')
        end_time: Optional end time timestamp
        start_time: Optional start time timestamp
    """
    pagination_opts = PaginationOpts(
        cursor=cursor,
        num_items=num_items,
    )
    
    params = {
        "paginationOpts": pagination_opts.to_dict()
    }
    
    if direction is not None:
        params["direction"] = direction
    if end_time is not None:
        params["endTime"] = end_time
    if start_time is not None:
        params["startTime"] = start_time
        
    return await run_convex_function(MCP_KEY, "lifelogs:paginatedDocs", params)


@app.tool()
async def search_markdown(
    query: str,
    cursor: Optional[str],
    num_items: int,
    end_time: Optional[int] = None,
    start_time: Optional[int] = None,
) -> Any:
    """
    Search the markdown.
    
    Args:
        query: Search query string (required)
        cursor: Cursor for pagination (required)
        num_items: Number of items to return (required)
        end_time: Optional end time timestamp
        start_time: Optional start time timestamp
    """
    pagination_opts = PaginationOpts(
        cursor=cursor,
        num_items=num_items,
    )
    
    params = {
        "query": query,
        "paginationOpts": pagination_opts.to_dict()
    }
    
    if end_time is not None:
        params["endTime"] = end_time
    if start_time is not None:
        params["startTime"] = start_time
        
    return await run_convex_function(MCP_KEY, "lifelogs:searchMarkdown", params)


@app.tool()
async def get_tools() -> list[types.Tool]:
    """
    Get a list of available tools and their specifications.
    """
    return await get_function_spec(deployment_info, MEMORIES_BY_IDENTIFIER)

if __name__ == "__main__":
    app.run()
