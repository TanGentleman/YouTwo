from src.yt_agent.agent import agent
from pprint import pprint

PROMPT_1 = "What is the capital of Italy? Don't use tools."
PROMPT_2 = "Use 3 chunks to answer: What is the definition of an evaluation?"

if __name__ == "__main__":
    agent.run(PROMPT_1)
    print("--------------------------------")
    pprint(agent.memory.get_succinct_steps())