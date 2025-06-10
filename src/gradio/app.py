import gradio as gr
from pathlib import Path
from rag import is_allowed_filetype, upload_file_to_vectara, retrieve_chunks
import logging

# ---------------------------
# Placeholder Backend Functions
# ---------------------------

def sync_lifelog_db() -> str:
    """
    Synchronizes local copy of lifelog (journal) database with the latest source.
    This function acts as a placeholder for database connection logic.

    Returns:
        str: Status message with sync timestamp.
    """
    import datetime
    return f"✅ Lifelog database synchronized successfully at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def search_lifelogs(keyword: str, date_start: str, date_end: str) -> str:
    """
    Searches for lifelog entries containing the provided keyword within the specified date range.

    Args:
        keyword (str): Search term to match against entries.
        date_start (str): Start date (YYYY-MM-DD format).
        date_end (str): End date (inclusive, YYYY-MM-DD format).

    Returns:
        str: Simulated search result summary. Replace with actual search logic.
    """
    return f"🔍 Found 12 entries related to ‘{keyword}’ between {date_start} and {date_end}."


def update_knowledge_graph_relations() -> str:
    """
    Updates the knowledge graph using the latest lifelog data.
    Simulates the creation of new triples (subject-predicate-object) from lifelog content.

    Returns:
        str: Update summary with number of relations added.
    """
    return "🧠 15 new triples have been added to the knowledge graph."


def natural_language_handler(query: str) -> str:
    """
    Processes natural language inputs to determine which system function to execute.
    Designed to interface with NLP/LLM for future automation.

    Args:
        query (str): Free-text input from the user.

    Returns:
        str: Simulated or generated action and result.
    """
    chunks, response = retrieve_chunks(query, limit=5)
    return f"💬 Got {len(chunks)} chunks for your request: “{query}”. Response: {response}"


def placeholder(feature_name: str = "unknown") -> str:
    """
    Placeholder for unimplemented features.

    Args:
        feature_name (str): Name of the feature to query.

    Returns:
        str: Placeholder response for future functions.
    """
    return f"{feature_name} functionality not available yet."  # Replace with dynamic logic later


# Gradio Behavior:
# Textbox: As input component: Passes text value as a str into the function.
# File: As input component: Passes the filepath to a temporary file object whose full path can be retrieved by file_obj.name
# If we change the type to "binary", uploaded_file returns bytes.
# NOTE: This means we can handle multiple files by tweaking this expected type.
def handle_file_input(file_path: str | None, uploaded_file: gr.File | None):
    if not uploaded_file and not file_path:
        return "Please enter a file path or upload a file."
    
    if uploaded_file:
        filepath = Path(uploaded_file.name)
    else:
        filepath = Path(file_path.strip())
        
    if not filepath.exists():
        logging.error(f"Error: The specified file path does not exist: {filepath}")
        return "Error: The uploaded filepath does not exist."
    
    if not is_allowed_filetype(filepath.suffix):
        return f"Error: The uploaded filetype {filepath.suffix} is not supported."
    
    # Obtain the bytes
    with open(filepath, "rb") as file:
        file_contents = file.read()
        
    
    upload_result = upload_file_to_vectara(file_contents, filepath.name)
    
    return f"Uploaded document: {upload_result['id']}"

# ---------------------------
# Gradio UI (Blocks API)
# ---------------------------

def get_gradio_blocks():
    with gr.Blocks(title="Knowledge Graph Agent Interface") as demo:
        gr.Markdown("## 🧠 Knowledge Graph Agent Interface\nBuilt with Gradio + MCP Support for LLM Tool Integration")

        # with gr.Tab("🔄 Sync Lifelog DB"):
        #     gr.Markdown("Synchronize the lifelog database locally.")
        #     sync_btn = gr.Button("Sync Database")
        #     sync_out = gr.Textbox(lines=2, label="Sync Status")
        #     sync_btn.click(fn=sync_lifelog_db, outputs=sync_out)

        # with gr.Tab("🔍 Search Lifelogs"):
        #     gr.Markdown("Search lifelog entries by keyword and time range.")
        #     keyword = gr.Textbox(label="Search Keyword")
        #     with gr.Row():
        #         start_date = gr.Textbox(label="Start Date (YYYY-MM-DD)")
        #         end_date = gr.Textbox(label="End Date (YYYY-MM-DD)")
        #     search_btn = gr.Button("Search Entries")
        #     search_out = gr.Textbox(label="Search Results")
        #     search_btn.click(fn=search_lifelogs, inputs=[keyword, start_date, end_date], outputs=search_out)

        # with gr.Tab("🧠 Update Knowledge Graph"):
        #     gr.Markdown("Use lifelog data to update knowledge graph relations.")
        #     update_btn = gr.Button("Update Graph")
        #     update_out = gr.Textbox(label="Update Status")
        #     update_btn.click(fn=update_knowledge_graph_relations, outputs=update_out)

        with gr.Tab("🗣️ Natural Language Mode"):
            gr.Markdown("Input natural language requests for system actions.")
            with gr.Row():
                user_query = gr.Textbox(label="Type your query")
            query_btn = gr.Button("Process Request")
            query_out = gr.Textbox(label="System Response")
            query_btn.click(fn=natural_language_handler, inputs=user_query, outputs=query_out)

        with gr.Tab("⚙️ Future Features"):
            gr.Markdown("Placeholder area for upcoming functionalities")
            feature = gr.Textbox(label="Feature to Check")
            feature_btn = gr.Button("Check Feature Status")
            feature_out = gr.Textbox(label="Status")
            feature_btn.click(fn=placeholder, inputs=feature, outputs=feature_out)

        with gr.Tab("🗣️Input File"):
            gr.Markdown("Input file")
            with gr.Row():
                file_path_input = gr.Textbox(label="Enter File Path")
                file_upload_input = gr.File(label="Upload a File", type="filepath")
            submit_btn = gr.Button("Submit")
            output = gr.Textbox(label="Result")
            submit_btn.click(fn=handle_file_input, inputs=[file_path_input, file_upload_input], outputs=output)

    return demo

# ---------------------------
# Launch as MCP Server
# ---------------------------
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    demo = get_gradio_blocks()
    demo.launch(mcp_server=True)