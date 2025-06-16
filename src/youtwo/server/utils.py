from typing import Any, Optional, Dict
from mcp.types import CallToolResult
import json
from youtwo.schemas import InitResult
import requests
import os

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
        return res

# API handling functions
async def async_convex_api_call(endpoint: str, method: str, data: dict = None, deployment_url: str | None = None) -> Optional[Dict[str, Any]]:
    """Make request to Convex API"""
    if deployment_url is None:
        # from dotenv import load_dotenv
        # load_dotenv()
        convex_url = os.getenv("CONVEX_URL")
        if not convex_url:
            raise ValueError("CONVEX_URL environment variable not set")
    else:
        convex_url = deployment_url
    deployment_url = f"{convex_url.replace('convex.cloud', 'convex.site').rstrip('/')}"
    try:
        assert deployment_url.endswith(".site"), "Convex HTTP api base must end with .site"
        url = f"{deployment_url}/{endpoint}"
        response = requests.request(
            method, url, json=data or {}, 
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API call failed: {str(e)}")
        return None