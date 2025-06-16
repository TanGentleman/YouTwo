import os

from dotenv import load_dotenv
from smolagents import CodeAgent, InferenceClientModel

from youtwo.agents.tools import inspect_database_tool, retrieve_tool

# Load environment variables
load_dotenv()
# Initialize models
model = InferenceClientModel(provider="nebius", model="nebius/deepseek-ai/DeepSeek-V3-0324-fast", api_key=os.environ["NEBIUS_API_KEY"])
agent = CodeAgent(
    tools=[
        retrieve_tool,
        inspect_database_tool,
    ],
    model=model,
    max_steps=2,
    verbosity_level=2,
    description="Agent used to search documents.",
)

if __name__ == "__main__":
    agent.run("What is 2+2?")
    messages = agent.memory.get_full_steps()
    print(messages)
