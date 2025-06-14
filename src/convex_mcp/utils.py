from typing import Any
from mcp.types import CallToolResult
import json
from src.schemas import InitResult

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

def parse_convex_result(res: CallToolResult) -> Any | None:
    try:
        p1 = json.loads(res.content[0].text)
        if p1["isError"]:
            raise ValueError(p1["error"])
        p2 = p1["content"][0]["text"]
        p3 = json.loads(p2)
        return p3["result"]
    except Exception as e:
        print(f"Error parsing convex result: {e}")
        return None