from youtwo.agents.agent import agent

PROMPT_1 = "What is the capital of Italy? Don't use tools."
PROMPT_2 = "Use 3 chunks to answer: What is the definition of an evaluation?"
PROMPT_3 = "Inspect the vector database. Tell me how many documents are in the database."

if __name__ == "__main__":
    agent.run(PROMPT_3, max_steps=1)
    print("--------------------------------")
    # pprint(agent.memory.get_succinct_steps())
