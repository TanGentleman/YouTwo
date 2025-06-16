# Run these scripts only from the root directory

from src.frontend.app import get_gradio_blocks

if __name__ == "__main__":
    blocks = get_gradio_blocks()
    blocks.launch()