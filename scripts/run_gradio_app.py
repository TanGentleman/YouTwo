# Run this gradio app with:
# python run_gradio_app.py

from src.frontend.app import get_gradio_blocks

if __name__ == "__main__":
    blocks = get_gradio_blocks()
    blocks.launch()
