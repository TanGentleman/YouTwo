from pathlib import Path
from typing import TypedDict

CONVEX_PROJECT_DIR = Path(__file__).parent.parent.parent / "backend"
ALLOWED_TOOLS = ["status", "functionSpec", "run"]
class InitResult(TypedDict):
    deploymentSelector: str
    url: str