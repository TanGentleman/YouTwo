import logging
from typing import Any, Optional
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP("Alert MCP")

def get_convex_url(load_dotenv: bool = True) -> str:
    """Get the HTTP URL for the Convex backend"""
    if load_dotenv:
        from dotenv import load_dotenv
        load_dotenv()
    backend_url = os.getenv("CONVEX_URL")
    if not backend_url:
        raise ValueError("CONVEX_URL not set in .env")
    backend_url = backend_url.replace(".convex.cloud", ".convex.site")
    if not backend_url.endswith(".convex.site"):
        raise ValueError("CONVEX_URL is not a valid Convex URL")
    return backend_url

@app.tool()
def send_notification(
    title: str,
    message: str,
    severity: Optional[str] = "info",
    fields: Optional[list[dict[str, Any]]] = None,
    providers: Optional[list[str]] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Send a notification via HTTP POST to the /ping webhook endpoint.
    
    Args:
        title: Notification title
        message: Notification message
        severity: Notification severity level (info, success, warning, error)
        fields: Optional list of field objects with name, value, and optional inline boolean
        providers: Optional list of notification providers (slack, discord)
        timeout: Request timeout in seconds
    
    Returns:
        Response dictionary from the webhook
    
    Raises:
        requests.RequestException: If the HTTP request fails
        ValueError: If the response indicates an error or CONVEX_HTTP_URL not set
    """
    # Get the Convex HTTP URL (throws error if not set)
    base_url = get_convex_url()
    webhook_url = f"{base_url}/ping"
    
    payload = {
        "title": title,
        "message": message,
    }
    
    if severity:
        payload["severity"] = severity
    if fields:
        payload["fields"] = fields
    if providers:
        payload["providers"] = providers
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Check if the webhook returned an error
        if not result.get("success", True) and "error" in result:
            raise ValueError(f"Webhook error: {result['error']}")
        
        return result
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to send notification: {e}")


if __name__ == "__main__":
    app.run()
