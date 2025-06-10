import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from fastrtc import (
    get_stt_model,
    get_tts_model,
    Stream,
    ReplyOnPause,
    # get_twilio_turn_credentials,
)
from smolagents import CodeAgent, InferenceClientModel, tool

from rag import retrieve_chunks

# Load environment variables
load_dotenv()

# Initialize file paths
curr_dir = Path(__file__).parent

# Initialize models
# stt_model = get_stt_model()
# tts_model = get_tts_model()
model = InferenceClientModel(provider="nebius", model="nebius/Qwen/Qwen3-30B-A3B", api_key=os.environ["NEBIUS_API_KEY"])
# Conversation state to maintain history
conversation_state: List[Dict[str, str]] = []

# System prompt for agent
system_prompt = """You are a general-purpose chatbot that answers user questions using information from uploaded documents. 
When a question requires document-based information:
1. Use the retrieval tool to fetch relevant document chunks
2. Synthesize answers using these chunks
3. Always cite your document sources

If information isn't in documents, use your general knowledge but state this limitation.
"""



@tool
def retrieve_tool(query: str, limit: int = 5) -> list[dict]:
    """
    Retrieve chunks by relevance to a query

    Args:
        query: The query to retrieve chunks for
        limit: The maximum number of chunks to retrieve (default: 5)

    Returns:
        A list of chunks
    """
    return retrieve_chunks(query, limit)

agent = CodeAgent(
    tools=[
        retrieve_tool,
    ],
    model=model,
    max_steps=2,
    verbosity_level=2,
    description="Search the YouTwo architecture documentation for information.",
)

# def process_response(audio):
#     """Process audio input and generate LLM response with TTS"""
#     # Convert speech to text using STT model
#     text = stt_model.stt(audio)
#     if not text.strip():
#         return

#     input_text = f"{system_prompt}\n\n{text}"
#     # Get response from agent
#     response_content = agent.run(input_text)

#     # Convert response to audio using TTS model
#     for audio_chunk in tts_model.stream_tts_sync(response_content or ""):
#         # Yield the audio chunk
#         yield audio_chunk


# stream = Stream(
#     handler=ReplyOnPause(process_response, input_sample_rate=16000),
#     modality="audio",
#     mode="send-receive",
#     ui_args={
#         "pulse_color": "rgb(255, 255, 255)",
#         "icon_button_color": "rgb(255, 255, 255)",
#         "title": "🧑‍💻The YouTwo Agent",
#     },
#     # rtc_configuration=get_twilio_turn_credentials(),
#     rtc_configuration = {"iceServers": [{"urls": "stun:stun.l.google.com:19302"}]}
# )

if __name__ == "__main__":
    # stream.ui.launch(server_port=7861)
    agent.run("What is 2+2?")
    messages = agent.memory.get_full_steps()
    print(messages)