import os

from dotenv import load_dotenv
from smolagents import CodeAgent, InferenceClientModel

from src.yt_agent.tools import retrieve_tool
from src.yt_agent.prompts import AGENTIC_MODE_SYSTEM_PROMPT

# Load environment variables
load_dotenv()
# Initialize models
model = InferenceClientModel(provider="nebius", model="nebius/Qwen/Qwen3-30B-A3B", api_key=os.environ["NEBIUS_API_KEY"])
agent = CodeAgent(
    tools=[
        retrieve_tool,
    ],
    model=model,
    max_steps=2,
    verbosity_level=2,
    description=AGENTIC_MODE_SYSTEM_PROMPT,
)

if __name__ == "__main__":
    # stream.ui.launch(server_port=7861)
    agent.run("What is 2+2?")
    messages = agent.memory.get_full_steps()
    print(messages)