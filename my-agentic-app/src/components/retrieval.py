from typing import List, Dict, Any
from langgraph import LangGraph
from convex import ConvexDB

def hybrid_search(query: str, vector_db: Any, keyword_index: Any) -> List[Dict[str, Any]]:
    vector_results = vector_db.search(query)
    keyword_results = keyword_index.search(query)

    combined_results = combine_results(vector_results, keyword_results)
    return combined_results

def combine_results(vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Combine and deduplicate results from both searches
    combined = {result['id']: result for result in vector_results + keyword_results}
    return list(combined.values())

def retrieve_documents(query: str) -> List[Dict[str, Any]]:
    vector_db = ConvexDB.get_vector_db()
    keyword_index = ConvexDB.get_keyword_index()

    results = hybrid_search(query, vector_db, keyword_index)
    return results

def process_retrieval(query: str) -> List[Dict[str, Any]]:
    documents = retrieve_documents(query)
    return documents