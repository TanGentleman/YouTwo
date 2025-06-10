# Citation: https://www.marktechpost.com/2025/05/15/a-step-by-step-guide-to-build-an-automated-knowledge-graph-pipeline-using-langgraph-and-networkx/
# import re

# Must import matplotlib to visualize the graph
# import matplotlib.pyplot as plt
from langgraph.graph.state import CompiledStateGraph
import networkx as nx
from typing import TypedDict, List, Tuple, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import requests
import os

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

# --- Helper Functions ---
import requests

def fetch_knowledge_graph():
    """Fetch knowledge graph from Convex HTTP API"""
    convex_url = os.getenv("CONVEX_URL")
    if not convex_url:
        raise ValueError("CONVEX_URL environment variable not set")
    # Ensure no trailing slash
    # If convex_url ends with .cloud or .cloud/, replace with .site
    if convex_url.endswith(".cloud/"):
        convex_url = convex_url[:-7] + ".site"
    elif convex_url.endswith(".cloud"):
        convex_url = convex_url[:-6] + ".site"
    if not convex_url.endswith(".site"):
       raise ValueError("CONVEX_URL must end with .site")
    api_url = f"{convex_url}/graph"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

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
    graph_data = fetch_knowledge_graph()
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
    
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(graph)

    nx.draw(graph, pos, with_labels=True, node_color='skyblue', node_size=1500, font_size=10)

    edge_labels = nx.get_edge_attributes(graph, 'relation')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)

    plt.title("Knowledge Graph")
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
def run_kg_pipeline(topic):
    initial_state = {
        "topic": topic,
        "raw_text": "",
        "entities": [],
        "relations": [],
        "resolved_relations": [],
        "graph": None,
        "validation": {},
        "messages": [],
        "current_agent": "data_gatherer"
    }
    graph = build_kg_graph()
    result = graph.invoke(initial_state)
    return result

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_kg_pipeline("Machine Learning")
    print(result)
    visualize_graph(result["graph"])