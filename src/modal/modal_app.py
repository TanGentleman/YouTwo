import os
import modal
from pathlib import Path
import sys

# Current directory path
curr_dir = Path(__file__).parent

# Create Modal image with required dependencies
web_image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "python-dotenv",
    "fastapi[standard]==0.115.4",
    "gradio[mcp]==5.33.0",
    "requests",
    # Add any other dependencies you need
).add_local_file(curr_dir / "app.py", "/root/app.py") \
.add_local_file(curr_dir / "schemas.py", "/root/schemas.py") \
.add_local_file(curr_dir / "rag.py", "/root/rag.py")

app = modal.App("youtwo-gradio", image=web_image)

# Modal limits
MAX_CONCURRENT_USERS = 20
MINUTES = 60  # seconds
TIME_LIMIT = 59 * MINUTES  # time limit (3540 seconds, just under the 3600s maximum)

# This volume will store any local files needed by the app
volume = modal.Volume.from_name("youtwo-volume", create_if_missing=True)

@app.function(
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("vectara")
    ],
    max_containers=1,
    scaledown_window=TIME_LIMIT,  # 3540 seconds, within the allowed 2-3600 second range
)
@modal.asgi_app()
def gradio_app():
    from fastapi import FastAPI
    from gradio.routes import mount_gradio_app
    
    # Add /root to path for imports
    sys.path.append("/root")
    
    # Import RAG functions
    # from rag import is_allowed_filetype, upload_file_to_vectara, retrieve_chunks
    from app import get_gradio_blocks
    
    # ---------------------------
    # Backend Functions
    # ---------------------------
    
    blocks = get_gradio_blocks()    # Mount Gradio app to FastAPI for Modal
    app = FastAPI()
    return mount_gradio_app(app=app, blocks=blocks, path="/")


if __name__ == "__main__":
    gradio_app.serve(mcp_server=True) 