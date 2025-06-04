# kg_pipeline.py
import re
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # For headless rendering

from typing import TypedDict, List, Tuple, Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph

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

# --- Agent Functions ---
def data_gatherer(state: KGState):
    # Simulate real data gathering
    collected_text = f"{state['topic']} is a core concept in technology and relates to entities: Machine Learning, Neural Networks, and Ethics. These components influence one another significantly."
    state["raw_text"] = collected_text
    state["messages"].append(HumanMessage(content="Completed data gathering from internal/external sources."))
    state["current_agent"] = "entity_extractor"
    return state

def entity_extractor(state: KGState):
    text = state["raw_text"]
    entities = re.findall(r"[A-Z][a-z]+(?: [A-Z][a-z]+)?", text)  # Basic extraction
    entities = list(set(entities))
    state["entities"] = entities
    state["messages"].append(HumanMessage(content=f"Identified {len(entities)} entities."))
    state["current_agent"] = "relation_extractor"
    return state

def relation_extractor(state: KGState):
    text = state["raw_text"]
    entities = state["entities"]
    relations = []
    # Example patterns
    relation_patterns = [("influences", r"(\w+(?: \w+)?) influences (\w+(?: \w+)?)")]
    for pattern, regex in relation_patterns:
        found = re.findall(regex, text, re.IGNORECASE)
        for s, o in found:
            relations.append((s, pattern, o))
    state["relations"] = relations
    state["messages"].append(HumanMessage(content=f"Detected {len(relations)} relationships."))
    state["current_agent"] = "entity_resolver"
    return state

def entity_resolver(state: KGState):
    # Simplify entity naming to reduce duplication
    resolved_relations = [(s.lower(), p, o.lower()) for s, p, o in state["relations"]]
    state["resolved_relations"] = resolved_relations
    state["messages"].append(HumanMessage(content="Resolved entity name inconsistencies."))
    state["current_agent"] = "graph_integrator"
    return state

def graph_integrator(state: KGState):
    G = nx.DiGraph()
    for s, p, o in state["resolved_relations"]:
        G.add_node(s)
        G.add_node(o)
        G.add_edge(s, o, label=p)
    state["graph"] = G
    state["messages"].append(HumanMessage(content="Graph structure built."))
    state["current_agent"] = "graph_validator"
    return state

def graph_validator(state: KGState):
    G = state["graph"]
    state["validation"] = {
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "acyclic": nx.is_directed_acyclic_graph(G),
    }
    state["messages"].append(HumanMessage(content="Validation completed."))
    state["current_agent"] = "__end__"
    return state

def router(state: KGState):
    return state["current_agent"]

# --- Pipeline Builder ---
def build_kg_graph():
    workflow = StateGraph(KGState)
    workflow.add_node("data_gatherer", data_gatherer)
    workflow.add_node("entity_extractor", entity_extractor)
    workflow.add_node("relation_extractor", relation_extractor)
    workflow.add_node("entity_resolver", entity_resolver)
    workflow.add_node("graph_integrator", graph_integrator)
    workflow.add_node("graph_validator", graph_validator)

    workflow.set_entry_point("data_gatherer")
    workflow.add_conditional_edges("data_gatherer", router, {"entity_extractor": "entity_extractor"})
    workflow.add_conditional_edges("entity_extractor", router, {"relation_extractor": "relation_extractor"})
    workflow.add_conditional_edges("relation_extractor", router, {"entity_resolver": "entity_resolver"})
    workflow.add_conditional_edges("entity_resolver", router, {"graph_integrator": "graph_integrator"})
    workflow.add_conditional_edges("graph_integrator", router, {"graph_validator": "graph_validator"})
    workflow.add_conditional_edges("graph_validator", router, {"__end__": "__end__"})

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