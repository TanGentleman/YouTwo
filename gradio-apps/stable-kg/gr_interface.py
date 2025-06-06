# gr_interface.py
import gradio as gr
from kg_pipeline import run_kg_pipeline
from io import BytesIO
import matplotlib.pyplot as plt
import networkx as nx
from base64 import b64encode
from typing import Any

def generate_knowledge_graph(topic: str) -> tuple[str, str, Any]:
    result = run_kg_pipeline(topic)

    # Format messages
    message_log = "\n".join([str(m.content) for m in result["messages"]])

    # Format validation summary
    validation_info = f"{result['validation']}"

    # Generate graph image
    G = result["graph"]
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, edge_color="gray")
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Save image to buffer
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()
    img_bytes.seek(0)

    # Convert image to Base64 for Gradio
    image_b64 = b64encode(img_bytes.read()).decode('utf-8')
    image_data = f"data:image/png;base64,{image_b64}"

    return message_log, validation_info, image_data

# ------------------
# Gradio Interface
# ------------------

with gr.Blocks(title="LangGraph Knowledge Graph Agent") as demo:
    gr.Markdown("## 🧠 Knowledge Graph Builder with LangGraph + Gradio")
    gr.Markdown("Trigger a full knowledge graph generation pipeline using multiple AI agents.")

    with gr.Row():
        topic_input = gr.Textbox(label="Topic", placeholder="Enter a topic (e.g., 'Artificial Intelligence')")

    with gr.Row():
        run_btn = gr.Button("🧠 Build Knowledge Graph")

    with gr.Row():
        output_log = gr.Textbox(lines=6, label="Pipeline Progress")
        output_validation = gr.JSON(label="Graph Validation Results")
    
    with gr.Row():
        graph_image = gr.Image(label="Generated Knowledge Graph", type="pil")

    run_btn.click(
        fn=generate_knowledge_graph,
        inputs=[topic_input],
        outputs=[output_log, output_validation, graph_image]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(mcp_server=True)