from pprint import pprint
import gradio as gr
from pathlib import Path
from src.yt_rag.rag import is_allowed_filetype, upload_file_to_vectara, retrieve_chunks
import logging
from src.yt_agent.agent import agent
# ---------------------------
# Placeholder Backend Functions
# ---------------------------


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

def agent_handler(query: str) -> str:
    """
    Placeholder for unimplemented features.

    Args:
        feature_name (str): Name of the feature to query.

    Returns:
        str: Placeholder response for future functions.
    """
    response = agent.run(query)

    print("Raw Response:\n", response)
    if isinstance(response, dict):
        parsed_response = response.get("output") or response.get("answer") or str(response)
    else:
        parsed_response = str(response)
    print("\nParsed Agent Response:\n", parsed_response)

    messages = agent.memory.get_succinct_steps()
    print("\nParsed messages:")
    print("**********")
    pprint(messages)
    return f"💬 Response Output: {parsed_response}"

def placeholder(feature_name: str = "unknown") -> str:
    """
    Placeholder for unimplemented features.

    Args:
        feature_name (str): Name of the feature to query.

    Returns:
        str: Placeholder response for future functions.
    """
    return f"{feature_name} functionality not available yet."  # Replace with dynamic logic later

def agent_chat(message: str, chat_history: tuple[str, str]):
    if not message.strip():
        return chat_history, ""

    # Add user message to chat
    #chat_history.append({"role": "user", "content": message})

    # Append user message to history
    #chat_history = chat_history or []
    chat_history.append(("You", message))

    # Run your agent
    agent_response = agent_handler(message)

    # Append agent response to history
    #chat_history.append({"role": "assistant", "content": agent_response})
    chat_history.append(("Agent", agent_response))

    return chat_history, ""

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

        with gr.Tab("🗣️ Natural Language Mode"):
            gr.Markdown("Input natural language requests for system actions.")
            with gr.Row():
                user_query = gr.Textbox(label="Type your query")
            query_btn = gr.Button("Process Request")
            query_out = gr.Textbox(label="System Response")
            query_btn.click(fn=natural_language_handler, inputs=user_query, outputs=query_out)

        with gr.Tab("⚙️ Simple Agent"):
            gr.Markdown("Agentic Question and Answer")
            feature = gr.Textbox(label="Feature to Check")
            feature_btn = gr.Button("Check Feature Status")
            feature_out = gr.Textbox(label="Status")
            feature_btn.click(fn=placeholder, inputs=feature, outputs=feature_out)
            feature_btn.click(fn=agent_handler, inputs=feature, outputs=feature_out)
        
        with gr.Tab("⚙️ Agentic Chat"):
            gr.Markdown("Agentic Question and Answer1")
            chatbot = gr.Chatbot(label="KG Agent", height=500, show_label=True, container=True,
                bubble_full_width=False,
                value=[
                    (None, "👋 Hello! I'm the KG Agent, your intelligent assistant for serving KG. How can I help you today?")
                ])
            user_input = gr.Textbox(placeholder="Type your question...", label="Message", lines=2, scale=4, show_label=False)
            #clear_button = gr.Button("🗑️ Clear Chat", size="sm")
            send_btn = gr.Button("Send", variant="primary", scale=1)

            # Wire up the button (and hitting Enter) to call `agent_chat`
            send_btn.click(
                fn=agent_chat,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input],
                show_progress=True
            )
            user_input.submit(
                fn=agent_chat,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input],
                #outputs=[self.chatbot, self.message_input, self.context_display, self.suggestions_display],
            )

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