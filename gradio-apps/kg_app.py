import gradio as gr
from typing import List, Dict, Tuple

# Simulated lifelog entry type
Lifelog = Dict[str, str]

# ---------------------------
# Placeholder Backend Functions: Now return structured data
# ---------------------------

def sync_lifelog_db() -> str:
    import datetime
    return f"✅ Lifelog database synchronized at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def search_lifelogs(keyword: str, date_start: str, date_end: str) -> List[Lifelog]:
    # Simulated response: mock lifelogs containing markdown and IDs
    return [
        {
            "id": "log_1",
            "content": "# My Morning Thoughts\nToday, I learned about **EntityA** and **EntityB**. It turns out that EntityA influences EntityB.",
            "startTime": "2024-01-01T08:30:00",
            "endTime": "2024-01-01T09:00:00",
            "embeddingId": "emb_001"
        },
        {
            "id": "log_2",
            "content": "# Later Notes\nEntityC is a special type of EntityB that I observed yesterday at the park.",
            "startTime": "2024-01-02T14:00:00",
            "endTime": "2024-01-02T14:30:00",
            "embeddingId": "emb_002"
        }
    ]

def submit_kg_triples(triples: List[Tuple[str, str, str]]) -> int:
    # Simulated backend for storing triples
    return len(triples)  # return number of triples added

def placeholder(feature_name: str):
    return f"💡 [Placeholder {feature_name}]: Feature not yet implemented."

# ---------------------------
# Gradio UI
# ---------------------------

with gr.Blocks(title="Knowledge Graph Agent Interface") as demo:
    gr.Markdown("## 🧠 Knowledge Graph Agent Interface\nBuilt with Gradio + MCP | Powered by Serverless Lifelog Backend")

    # --- TAB: Update Knowledge Graph ---
    with gr.Tab("🧠 Update Knowledge Graph"):
        gr.Markdown("Build and update a knowledge graph using lifelogs from your journal.")
        update_btn = gr.Button("Generate Knowledge Graph from All Lifelogs")
        update_out = gr.Textbox(label="Update Summary")

        def update_knowledge_graph_relations():
            # 1. Get all lifelogs (simulated via mock serverless function)
            entries = search_lifelogs("", "1900-01-01", "2100-01-01")

            # 2. Process each entry into the knowledge graph
            all_relations = []
            for entry in entries:
                try:
                    from kg_pipeline import build_kg_graph, run_knowledge_graph_pipeline_from_text
                    # Start processing from the pipeline using the content of the journal
                    kg_state = run_knowledge_graph_pipeline_from_text(entry["content"])

                    # Append resolved triples from this entry
                    all_relations.extend(kg_state["resolved_relations"])

                except Exception as e:
                    return f"⚠️ Error processing one lifelog: {e}"

            # 3. Submit resulting triples to backend
            total_added = submit_kg_triples(all_relations)

            # 4. Output message
            return f"✅ Total of **{total_added}** new triples added to the knowledge graph."

        # Wire button to function
        update_btn.click(fn=update_knowledge_graph_relations, outputs=update_out)

# ---------------------------
# Launch App
# ---------------------------
if __name__ == "__main__":
    demo.launch(mcp_server=True)