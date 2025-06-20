import json
import os
from typing import Any, Dict, Optional

import requests
from mcp.types import CallToolResult

from youtwo.exceptions import ToolCallError
from youtwo.schemas import InitResult


async def parse_status(status_output: CallToolResult) -> InitResult | None:
    if not status_output.content:
        return None
    try:
        data = json.loads(status_output.content[0].text)
        for dep in data.get("availableDeployments", []):
            if dep.get("kind") == "ownDev":
                return {
                    "deploymentSelector": dep.get("deploymentSelector"),
                    "url": dep.get("url"),
                }
    except Exception as e:
        print(f"Error parsing status: {e}")
    return None


def dictify_tool_call(input: CallToolResult) -> dict:
    """
    Strips the tool call from the input.

    Raises ToolCallError if the tool call is an error.
    """
    if input.isError:
        raise ToolCallError(input.content[0].text)
    return json.loads(input.content[0].text)


def parse_convex_result(res: CallToolResult) -> Any | None:
    try:
        full_dict = dictify_tool_call(res)
        if full_dict["isError"]:
            raise ValueError(full_dict["error"])
        tool_results_str = full_dict["content"][0]["text"]
        convex_result_dict = json.loads(tool_results_str)
        return convex_result_dict["result"]
    except Exception as e:
        print(f"Error parsing convex result: {e}")
        return res


def get_convex_url(force_load_dotenv: bool = False) -> str:
    if force_load_dotenv:
        from dotenv import load_dotenv

        load_dotenv()
    convex_url = os.getenv("CONVEX_URL")
    if not convex_url:
        raise ValueError("CONVEX_URL environment variable not set")
    deployment_url = f"{convex_url.replace('convex.cloud', 'convex.site').rstrip('/')}"
    return deployment_url


# API handling functions
async def async_convex_api_call(
    endpoint: str, method: str, data: dict = None, deployment_url: str | None = None
) -> Optional[Dict[str, Any]]:
    """Make request to Convex API"""
    if deployment_url is None:
        convex_url = get_convex_url()
    else:
        convex_url = deployment_url
    deployment_url = f"{convex_url.replace('convex.cloud', 'convex.site').rstrip('/')}"
    try:
        if not deployment_url.endswith(".site"):
            raise ValueError("Convex HTTP api base must end with .site")
        url = f"{deployment_url}/{endpoint}"
        response = requests.request(
            method, url, json=data or {}, headers={"Content-Type": "application/json"}, timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API call failed: {str(e)}")
        return None
