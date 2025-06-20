import asyncio
import logging
from pathlib import Path

import gradio as gr

from youtwo.agents.agent import kg_management_agent as agent
from youtwo.agents.prompts import KG_MANAGEMENT_TASK, KG_MANAGEMENT_PROMPT
from youtwo.memory.visualize import visualize_knowledge_graph
from youtwo.paths import DATA_DIR
from youtwo.rag.vectara_client import VectaraClient, is_allowed_filetype
from youtwo.server.config import USER_DEFAULT_MESSAGE
from smolagents import ActionStep, FinalAnswerStep, PlanningStep, RunResult, ChatMessageStreamDelta
# ---------------------------
# Placeholder Backend Functions
# ---------------------------
INITIAL_ASSISTANT_MESSAGE = KG_MANAGEMENT_PROMPT
PREFILLED_HUMAN_MESSAGE = USER_DEFAULT_MESSAGE


def natural_language_handler(query: str) -> str:
    """
    Processes natural language inputs to determine which system function to execute.
    Designed to interface with NLP/LLM for future automation.

    Args:
        query (str): Free-text input from the user.

    Returns:
        str: Simulated or generated action and result.
    """
    client = VectaraClient()
    chunks, response = client.retrieve_chunks(query, limit=5)
    return f"*Retrieved {len(chunks)} chunks.*\n------\n{response}"


def agent_chat(message: str, chat_history):
    if not message.strip():
        return chat_history, ""

    # Append user message to history
    context_str = "\n\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[:2]])
    chat_history.append({"role": "user", "content": message})
    task = KG_MANAGEMENT_TASK.format(context=context_str, user_input=message)

    STREAM = True
    if STREAM:
        steps = []
        # Run your agent
        stream_response_string = ""
        for step in agent.run(task, stream=True):
            if isinstance(step, ActionStep):
                step_string = step.model_output or "Empty action step"
                # print("Action step: ", step_string[50:])
                steps.append(step_string)
            elif isinstance(step, FinalAnswerStep):
                # print("Truncating final answer")
                step_string = str(step.output)
                # print("Final answer: ", step_string[50:])
                steps.append(step_string)
            elif isinstance(step, PlanningStep):
                step_string = step.model_output_message.content or "Empty planning step"
                # print("Planning step: ", step_string[50:])
                steps.append(step_string)
            elif isinstance(step, RunResult):
                step_string = str(step.output)
                # print("Run result: ", step_string[:50])
                steps.append(step_string)
            elif isinstance(step, ChatMessageStreamDelta):
                step_string = step.content or ""
                # print("Chat message stream delta: ", step_string[:50])
                stream_response_string += step_string
            else:
                # if isinstance(step, str):
                #     stream_response_string += step
                # else:
                print("Unknown step: ", str(step))
        response = steps[-1] or stream_response_string
    else:
        response = agent.run(task)
    
    if isinstance(response, dict):
        parsed_response = (
            response.get("output") or response.get("answer") or str(response)
        )
    else:
        parsed_response = str(response)

    # Append agent response to history
    chat_history.append({"role": "assistant", "content": parsed_response})

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

    client = VectaraClient()
    # Obtain the bytes
    with open(filepath, "rb") as file:
        file_contents = file.read()

    upload_result = client.upload_file(file_contents, filepath.name)

    return f"Uploaded document: {upload_result['id']}"

# Add visualize button handler
def handle_visualize():
    try:
        # Run the async function
        visualization_path, data_path = asyncio.run(visualize_knowledge_graph())
        
        result_msg = f"✅ Knowledge graph visualization generated successfully!\nVisualization saved to: {visualization_path}"
        if data_path:
            result_msg += f"\nData saved to: {data_path}"
        
        return gr.update(value=result_msg, visible=True)
    except Exception as e:
        return gr.update(value=f"❌ Error generating visualization: {str(e)}", visible=True)

def handle_load_graph():
    # read the image from DATA_DIR / knowledge_graph.png
    graph_image_file = DATA_DIR / "knowledge_graph.png"
    if not graph_image_file.exists():
        return gr.update(value="❌ Error loading graph image", visible=True), None
    return gr.update(value="✅ Graph Image Loaded", visible=True), gr.Image(value=graph_image_file, visible=True)

# ---------------------------
# Gradio UI (Blocks API)
# ---------------------------


def get_gradio_blocks():
    with gr.Blocks(title="YouTwo Memory Agent Interface", analytics_enabled=False) as demo:
        gr.Markdown(
            "## 🧠 YouTwo Memory Agent Interface\nBuilt with Gradio + MCP Support for LLM Tool Integration"
        )
        with gr.Tab("🔍 Visualize"):
            gr.Markdown("Visualize the knowledge graph")
            
            visualize_btn = gr.Button("🔍 Generate Image", variant="primary")
            visualization_output = gr.Textbox(
                label="Image Status",
                visible=False,
                interactive=False
            )
            
            graph_image = gr.Image(
                label="Knowledge Graph",
                type="filepath",
                height=700,
                show_download_button=True,
                show_fullscreen_button=True,
                interactive=False
            )
            
            # Wire up the visualize button
            visualize_btn.click(
                fn=handle_load_graph,
                outputs=[visualization_output, graph_image],
            )
        with gr.Tab("⚙️ Agentic Chat"):
            gr.Markdown("Chat using memory tools")
            chatbot = gr.Chatbot(
                label="YT Agent",
                height=500,
                show_label=True,
                container=True,
                type="messages",
                bubble_full_width=False,
                value=[
                    {
                        "role": "assistant",
                        "content": INITIAL_ASSISTANT_MESSAGE,
                    }
                ],
            )
            visualization_output = gr.Textbox(
                label="Visualization Status",
                visible=False,
                interactive=False
            )
            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Type your question...",
                    label="Message",
                    lines=2,
                    scale=4,
                    show_label=False,
                    value=PREFILLED_HUMAN_MESSAGE,
                )
                with gr.Column(scale=1):
                    send_btn = gr.Button("Send", variant="primary")
                    visualize_btn = gr.Button("🔍 Visualize", variant="secondary")

            # Wire up the button (and hitting Enter) to call `agent_chat`
            send_btn.click(
                fn=agent_chat,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input],
                show_progress=True,
            )
            user_input.submit(
                fn=agent_chat,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input],
                # outputs=[self.chatbot, self.message_input, self.context_display, self.suggestions_display],
            )
            
            
            visualize_btn.click(
                fn=handle_visualize,
                outputs=[visualization_output],
            )
        with gr.Tab("🗣️ Grounded Q&A"):
            gr.Markdown("Input natural language requests for system actions.")
            with gr.Row():
                user_query = gr.Textbox(label="Type your query")
            query_btn = gr.Button("Process Request")
            query_out = gr.Textbox(label="System Response")
            query_btn.click(
                fn=natural_language_handler, inputs=user_query, outputs=query_out
            )

        with gr.Tab("🗣️Input File"):
            gr.Markdown("Input file")
            with gr.Row():
                file_path_input = gr.Textbox(label="Enter File Path")
                file_upload_input = gr.File(label="Upload a File", type="filepath")
            submit_btn = gr.Button("Submit")
            output = gr.Textbox(label="Result")
            submit_btn.click(
                fn=handle_file_input,
                inputs=[file_path_input, file_upload_input],
                outputs=output,
            )

    return demo


# ---------------------------
# Launch as MCP Server
# ---------------------------
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    demo = get_gradio_blocks()
    demo.launch(mcp_server=True)
