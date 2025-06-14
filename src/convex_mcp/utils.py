from mcp.types import CallToolResult
import json
from src.convex_mcp.config import InitResult

async def parse_status(statusOutput: CallToolResult) -> InitResult | None:
    if not statusOutput.content: return None
    try:
        data = json.loads(statusOutput.content[0].text)
        for dep in data.get("availableDeployments", []):
            if dep.get("kind") == "ownDev":
                return {"deploymentSelector": dep.get("deploymentSelector"), "url": dep.get("url")}
    except Exception as e:
        print(f"Error parsing status: {e}")
    return None