import logging
import json
import requests
from typing import List, Dict, Any, Optional, TypedDict

from mcp.server.fastmcp import FastMCP, Context

# from vectara import (
#     SearchCorporaParameters, GenerationParameters, CitationParameters,
#     KeyedSearchCorpus, ContextConfiguration
# )

# Custom parameter classes to replace Vectara imports
class ContextConfiguration:
    def __init__(self, sentences_before: int = 2, sentences_after: int = 2):
        self.sentences_before = sentences_before
        self.sentences_after = sentences_after

class KeyedSearchCorpus:
    def __init__(self, corpus_key: str, lexical_interpolation: float = 0.005):
        self.corpus_key = corpus_key
        self.lexical_interpolation = lexical_interpolation

class SearchCorporaParameters:
    def __init__(
        self, 
        corpora: List[KeyedSearchCorpus],
        context_configuration: ContextConfiguration,
        limit: int = 10,
    ):
        self.corpora = corpora
        self.context_configuration = context_configuration
        self.limit = limit

class CitationParameters:
    def __init__(self, style: Optional[str] = None, url_pattern: Optional[str] = None):
        self.style = style
        self.url_pattern = url_pattern

class GenerationParameters:
    def __init__(
        self,
        response_language: str = "eng",
        max_used_search_results: int = 10,
        generation_preset_name: str = "vectara-summary-table-md-query-ext-jan-2025-gpt-4o",
        citations: Optional[CitationParameters] = None,
        enable_factual_consistency_score: bool = True,
    ):
        self.response_language = response_language
        self.max_used_search_results = max_used_search_results
        self.generation_preset_name = generation_preset_name
        self.citations = citations or CitationParameters()
        self.enable_factual_consistency_score = enable_factual_consistency_score

class VectaraClient:
    """Simple client to replace the Vectara package"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def query(self, query: str, search: SearchCorporaParameters, generation: Optional[GenerationParameters] = None, save_history: bool = True):
        """Execute a query against Vectara API"""
        # Get the first corpus key from search parameters
        corpus_key = search.corpora[0].corpus_key if search.corpora else "default"
        
        url = f"https://api.vectara.io/v2/corpora/{corpus_key}/query"
        headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Build payload based on search and generation parameters
        payload = {
            "query": query,
            "search": {
                "limit": search.limit,
            },
            "save_history": save_history,
            "stream_response": False,
        }
        
        if generation:
            payload["generation"] = {
                "generation_preset_name": generation.generation_preset_name,
                "max_used_search_results": generation.max_used_search_results,
                "response_language": generation.response_language,
                "enable_factual_consistency_score": generation.enable_factual_consistency_score,
            }
            
            if generation.citations:
                payload["generation"]["citations"] = {
                    "style": generation.citations.style,
                    "url_pattern": generation.citations.url_pattern
                }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Process response
        response_data = response.json()
        
        # Create a simple result object with summary field
        class QueryResult:
            def __init__(self, summary: str):
                self.summary = summary
                
        if generation and "summary" in response_data:
            return QueryResult(summary=response_data["summary"])
        elif "search_results" in response_data:
            # If no generation, construct a summary from search results
            results = [r.get("text", "") for r in response_data.get("search_results", [])]
            return QueryResult(summary="\n\n".join(results))
        else:
            return QueryResult(summary="No results found")

    def upload_file(self, file_bytes: bytes, filename: str, corpus_key: str):
        """Upload a file to Vectara"""
        url = f"https://api.vectara.io/v2/corpora/{corpus_key}/upload_file"
        
        headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key,
        }
        
        content_type = "application/pdf"
        if filename.endswith(".doc") or filename.endswith(".docx"):
            content_type = "application/msword"
        elif filename.endswith(".txt"):
            content_type = "text/plain"
        elif filename.endswith(".html"):
            content_type = "text/html"
            
        files = {
            'file': (filename, file_bytes, content_type)
        }
        
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vectara-mcp-server")

# Create the Vectara MCP server
mcp = FastMCP("vectara")

def get_search_config(
    corpus_keys: list[str],
    n_sentences_before: int,
    n_sentences_after: int,
    lexical_interpolation: float,
):
    search_params = SearchCorporaParameters(
        corpora=[
            KeyedSearchCorpus(
                corpus_key=corpus_key,
                lexical_interpolation=lexical_interpolation
            ) for corpus_key in corpus_keys
        ],
        context_configuration=ContextConfiguration(
            sentences_before=n_sentences_before,
            sentences_after=n_sentences_after,
        ),
        limit=100,
    )
    return search_params

def get_generation_config(
    generation_preset_name: str,
    max_used_search_results: int,
    response_language: str,
) -> GenerationParameters:
    generation_params = GenerationParameters(
        response_language=response_language,
        max_used_search_results=max_used_search_results,
        generation_preset_name=generation_preset_name,
        citations=CitationParameters(style="markdown", url_pattern="{doc.url}"),
        enable_factual_consistency_score=True,
    )
    return generation_params

# Query tool
@mcp.tool()
async def ask_vectara(
    query: str,
    ctx: Context,
    corpus_keys: list[str] = [],
    api_key: str = "",
    n_sentences_before: int = 2,
    n_sentences_after: int = 2,
    lexical_interpolation: float = 0.005,
    max_used_search_results: int = 10,
    generation_preset_name: str = "vectara-summary-table-md-query-ext-jan-2025-gpt-4o",
    response_language: str = "eng",
) -> str:
    """
    Run a RAG query using Vectara, returning search results with a generated response.

    Args:
        query: str, The user query to run - required.
        corpus_keys: list[str], List of Vectara corpus keys to use for the search - required. Please ask the user to provide one or more corpus keys. 
        api_key: str, The Vectara API key - required.
        n_sentences_before: int, Number of sentences before the answer to include in the context - optional, default is 2.
        n_sentences_after: int, Number of sentences after the answer to include in the context - optional, default is 2.
        lexical_interpolation: float, The amount of lexical interpolation to use - optional, default is 0.005.
        max_used_search_results: int, The maximum number of search results to use - optional, default is 10.
        generation_preset_name: str, The name of the generation preset to use - optional, default is "vectara-summary-table-md-query-ext-jan-2025-gpt-4o".
        response_language: str, The language of the response - optional, default is "eng".

    Returns:
        The response from Vectara, including the generated answer and the search results.
    """
    if not query:
        return "Query is required."
    if not corpus_keys:
        return "Corpus keys are required. Please ask the user to provide one or more corpus keys."
    if not api_key:
        return "API key is required. Please provide your Vectara API key."

    if ctx:
        ctx.info(f"Running Vectara RAG query: {query}")
    try:
        client = VectaraClient(api_key=api_key)
        if ctx:
            await ctx.report_progress(0, 1)
        res = client.query(
            query=query,
            search=get_search_config(
                corpus_keys=corpus_keys,
                n_sentences_before=n_sentences_before,
                n_sentences_after=n_sentences_after,
                lexical_interpolation=lexical_interpolation,
            ),
            generation=get_generation_config(
                generation_preset_name=generation_preset_name,
                max_used_search_results=max_used_search_results,
                response_language=response_language,
            ),
            save_history=True,
        )
        if ctx:
            await ctx.report_progress(1, 1)
        return res.summary
    except Exception as e:
        return f"Error with Vectara RAG query: {str(e)}"


# Query tool
@mcp.tool()
async def search_vectara(
    query: str,
    ctx: Context,
    corpus_keys: list[str] = [],
    api_key: str = "",
    n_sentences_before: int = 2,
    n_sentences_after: int = 2,
    lexical_interpolation: float = 0.005
) -> str:
    """
    Run a semantic search query using Vectara, without generation.

    Args:
        query: str, The user query to run - required.
        corpus_keys: list[str], List of Vectara corpus keys to use for the search - required. Please ask the user to provide one or more corpus keys. 
        api_key: str, The Vectara API key - required.
        n_sentences_before: int, Number of sentences before the answer to include in the context - optional, default is 2.
        n_sentences_after: int, Number of sentences after the answer to include in the context - optional, default is 2.
        lexical_interpolation: float, The amount of lexical interpolation to use - optional, default is 0.005.
    
    Returns:
        The response from Vectara, including the matching search results.
    """
    if not query:
        return "Query is required."
    if not corpus_keys:
        return "Corpus keys are required. Please ask the user to provide one or more corpus keys."
    if not api_key:
        return "API key is required. Please provide your Vectara API key."

    if ctx:
        ctx.info(f"Running Vectara semantic search query: {query}")
    try:
        client = VectaraClient(api_key=api_key)
        if ctx:
            await ctx.report_progress(0, 1)
        res = client.query(
            query=query,
            search=get_search_config(
                corpus_keys=corpus_keys,
                n_sentences_before=n_sentences_before,
                n_sentences_after=n_sentences_after,
                lexical_interpolation=lexical_interpolation,
            ),
            save_history=True,
        )
        if ctx:
            await ctx.report_progress(1, 1)
        return res.summary
    except Exception as e:
        return f"Error with Vectara semantic search query: {str(e)}"

@mcp.tool()
async def upload_to_vectara(
    file_bytes: bytes,
    filename: str,
    ctx: Context,
    corpus_key: str = "",
    api_key: str = "",
) -> str:
    """
    Upload a file to Vectara for processing.

    Args:
        file_bytes: bytes, The file content in bytes - required.
        filename: str, The name of the file - required.
        corpus_key: str, The Vectara corpus key - required.
        api_key: str, The Vectara API key - required.

    Returns:
        The response from Vectara, including the document ID and metadata.
    """
    if not file_bytes:
        return "File bytes are required."
    if not filename:
        return "Filename is required."
    if not corpus_key:
        return "Corpus key is required. Please provide a Vectara corpus key."
    if not api_key:
        return "API key is required. Please provide your Vectara API key."

    if ctx:
        ctx.info(f"Uploading file to Vectara: {filename}")
    try:
        client = VectaraClient(api_key=api_key)
        if ctx:
            await ctx.report_progress(0, 1)
        result = client.upload_file(file_bytes, filename, corpus_key)
        if ctx:
            await ctx.report_progress(1, 1)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error uploading to Vectara: {str(e)}"

def main():
    """Command-line interface for starting the Vectara MCP Server."""
    print("Starting Vectara MCP Server")
    mcp.run()

if __name__ == "__main__":
    main()