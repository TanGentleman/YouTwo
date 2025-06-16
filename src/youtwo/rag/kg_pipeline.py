# Citation: https://www.marktechpost.com/2025/05/15/a-step-by-step-guide-to-build-an-automated-knowledge-graph-pipeline-using-langgraph-and-networkx/
# import re

# Must import matplotlib to visualize the graph
# import matplotlib.pyplot as plt
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import networkx as nx
from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from youtwo.rag.backend import make_convex_api_call


# --- State Definition ---
class KGState(TypedDict):
    topic: str
    raw_text: str
    entities: List[str]
    relations: List[Tuple[str, str, str]]
    resolved_relations: List[Tuple[str, str, str]]
    graph: Any
    validation: Dict[str, Any]
    messages: List[Any]
    current_agent: str  # used by LangGraph state router
    frozen: bool # for experimental graph storage

# --- Helper Functions ---

def fetch_knowledge_graph(from_frozen = True):
    """Fetch knowledge graph from Convex HTTP API"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    if from_frozen:
        try:
            with open(f"knowledge_graph-{date_str}.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Knowledge graph file not found. Fetching from Convex...")
    knowledge_graph = make_convex_api_call("graph", "GET")
    with open(f"knowledge_graph-{date_str}.json", "w") as f:
        json.dump(knowledge_graph, f)
    return knowledge_graph

def prepare_graph_data(graph_data):
    """Convert Convex graph data to pipeline format"""
    entities = [
        {"id": e["id"], "name": e["name"], "type": e["entityType"]}
        for e in graph_data["entities"]
    ]

    relations = [
        (rel["from"], rel["relationType"], rel["to"])
        for rel in graph_data["relations"]
    ]

    return entities, relations

# --- Modified Agent Functions ---
def data_gatherer(state: KGState) -> KGState:
    print("📚 Data Gatherer: Fetching knowledge graph from Convex")
    # Replace in future with just the entities and relations relevant to the topic
    graph_data = fetch_knowledge_graph(state["frozen"])
    entities, relations = prepare_graph_data(graph_data)

    state["entities"] = entities
    state["relations"] = relations
    state["messages"].append(AIMessage(content="Fetched knowledge graph from Convex"))
    state["current_agent"] = "graph_integrator"

    return state

def graph_integrator(state: KGState) -> KGState:
    print("📊 Graph Integrator: Building the knowledge graph")
    G = nx.DiGraph()

    for s, p, o in state["relations"]:
        if not G.has_node(s):
            G.add_node(s)
        if not G.has_node(o):
            G.add_node(o)
        G.add_edge(s, o, relation=p)

    state["graph"] = G
    state["messages"].append(AIMessage(content=f"Built graph with {len(G.nodes)} nodes and {len(G.edges)} edges"))

    state["current_agent"] = "graph_validator"

    return state

def graph_validator(state: KGState) -> KGState:
    print("✅ Graph Validator: Validating knowledge graph")
    G = state["graph"]

    validation_report = {
        "num_nodes": len(G.nodes),
        "num_edges": len(G.edges),
        "is_connected": nx.is_weakly_connected(G) if G.nodes else False,
        "has_cycles": not nx.is_directed_acyclic_graph(G) if G.nodes else False
    }

    state["validation"] = validation_report
    state["messages"].append(AIMessage(content=f"Validation report: {validation_report}"))
    print(f"   Validation report: {validation_report}")

    state["current_agent"] = END

    return state

def visualize_graph(graph) -> None:
    """Visualize the knowledge graph using NetworkX and Matplotlib"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed. Please install it using 'pip install matplotlib'")
        return
    EXPERIMENTAL_GRAPH_VISUALIZATION = True

    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(graph)

    nx.draw(graph, pos, with_labels=True, node_color="skyblue", node_size=1500, font_size=10)

    edge_labels = nx.get_edge_attributes(graph, "relation")
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)

    plt.title("Knowledge Graph")
    if EXPERIMENTAL_GRAPH_VISUALIZATION:
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.2)
    else:
        plt.tight_layout()
    plt.show()

def build_kg_graph() -> CompiledStateGraph:
    workflow = StateGraph(KGState)

    workflow.add_node("data_gatherer", data_gatherer)
    workflow.add_node("graph_integrator", graph_integrator)
    workflow.add_node("graph_validator", graph_validator)

    workflow.add_edge("data_gatherer", "graph_integrator")
    workflow.add_edge("graph_integrator", "graph_validator")
    workflow.add_edge("graph_validator", END)

    workflow.set_entry_point("data_gatherer")
    return workflow.compile()


# --- Pipeline Execution Hook ---
def run_kg_pipeline(topic, frozen=True):
    initial_state = {
        "topic": topic,
        "raw_text": "",
        "entities": [],
        "relations": [],
        "resolved_relations": [],
        "graph": None,
        "validation": {},
        "messages": [],
        "current_agent": "data_gatherer",
        "frozen": frozen
    }
    graph = build_kg_graph()
    result = graph.invoke(initial_state)
    return result

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        result = run_kg_pipeline("Friends", frozen=False)
    else:
        result = run_kg_pipeline("Friends")

    print(result)
    visualize_graph(result["graph"])

if __name__ == "__main__":
    main()
