import os

from dotenv import load_dotenv
from smolagents import CodeAgent, InferenceClientModel

from youtwo.agents.tools import (
    add_observations,
    create_entities,
    create_relations,
    delete_entities,
    delete_relations,
    get_entities,
    get_graph,
    inspect_database_tool,
    retrieve_tool,
    visualize_custom_graph,
)

DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3-0324"
REASONING_MODEL = "deepseek-ai/DeepSeek-R1-0528"
LLAMA_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
# Load environment variables
load_dotenv()
# Initialize models
model = InferenceClientModel(
    provider="nebius",
    model_id=DEFAULT_MODEL,
    api_key=os.environ["NEBIUS_API_KEY"],
    max_tokens=2000,
)
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

# from youtwo.agents.prompts import VISUALIZER_AGENT_PROMPT
visualizer_agent = CodeAgent(
    tools=[
        visualize_custom_graph,
    ],
    stream_outputs=True,
    model=model,
    max_steps=2,
    description="Agent used to visualize knowledge graph.",
)

# from youtwo.agents.prompts import KG_MANAGEMENT_PROMPT
kg_management_agent = CodeAgent(
    tools=[
        get_entities,
        create_entities,
        delete_entities,
        create_relations,
        delete_relations,
        add_observations,
        get_graph,
        visualize_custom_graph,
    ],
    model=model,
    max_steps=2,
    stream_outputs=True,
    description="Agent for managing knowledge graph entities and relationships",
)

if __name__ == "__main__":
    agent.run("What is 2+2?")
    messages = agent.memory.get_full_steps()
    print(messages)
