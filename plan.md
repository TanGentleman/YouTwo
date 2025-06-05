
# Hackathon Huggingface

## Tracks:
*   **Track 1:** MCP Server Implementation
*   **Track 2:** Custom Agent Components
*   **Track 3:** Agentic Demo Showcase

## Core Idea: Gradio [UI] + Agent

## Proposed MVP Ideas:

### MVP Idea 1: Intelligent Document Q&A System

**Description:** A Gradio-based application where users can upload documents (PDFs, text files, etc.), and the system will automatically process them to enable intelligent Q&A. This MVP focuses on robust data ingestion, indexing, and retrieval.

**Key Features:**
*   **Document Upload:** Users can upload various document types.
*   **Automated Chunking & QA Generation:** Documents are automatically chunked, and Q&A pairs are generated from each chunk.
*   **Hybrid Search:** Utilizes both vector embeddings and keyword indexing for efficient retrieval.
*   **LLM Integration:** Leverages an LLM for generating concise and accurate answers based on retrieved context.

**Technology Stack:**
*   **Frontend:** Gradio
*   **Backend:** Python, LangGraph (for orchestration), Convex DB (for indexing and persistence), LLM (e.g., Hugging Face models)
*   **Data Sources:** PDF, text files (extensible to others like Slack, Google Drive)

**Placeholder Questions:**
*   How will we handle different document formats and their specific parsing challenges?
*   What is the strategy for generating high-quality Q&A pairs from document chunks?
*   How will we ensure the hybrid search effectively combines vector and keyword results?
*   What metrics will define the success of the Q&A accuracy?

### MVP Idea 2: Personalized Meeting Assistant

**Description:** An agentic system that assists users with personalized pre-meeting preparation and post-meeting documentation by leveraging audio data and transcripts.

**Key Features:**
*   **Audio Transcription:** Transcribes meeting audio into text.
*   **Key Information Extraction:** Identifies key discussion points, action items, and decisions.
*   **Personalized Summaries:** Generates concise summaries tailored to the user's role or interests.
*   **Knowledge Graph Integration (Stretch Goal):** Links meeting insights to a broader knowledge graph for richer context.

**Technology Stack:**
*   **Frontend:** Gradio (for interaction and display of summaries)
*   **Backend:** Python, Speech-to-Text models (e.g., Hugging Face ASR), LLM, Convex DB (for storing transcripts and extracted info)
*   **Data Sources:** Audio recordings, existing documentation (for context)

**Placeholder Questions:**
*   How will we handle speaker diarization for multi-person meetings?
*   What is the approach for extracting actionable insights from meeting transcripts?
*   How will the system personalize summaries effectively?
*   What are the privacy considerations for handling meeting audio and transcripts?

### MVP Idea 3: Automated Research Agent

**Description:** An agent that accepts a research question, searches a knowledge base, summarizes findings, cites sources, and highlights key information.

**Key Features:**
*   **Question Input:** Users provide a research question.
*   **Knowledge Base Search:** The agent searches across various data sources (e.g., indexed documents, web).
*   **Summarization & Citation:** Generates a comprehensive summary with proper citations.
*   **Key Information Highlighting:** Identifies and highlights critical details in the summary.

**Technology Stack:**
*   **Frontend:** Gradio
*   **Backend:** Python, LangGraph, LLM, Convex DB, potentially web scraping tools or APIs for external data.
*   **Data Sources:** Indexed internal documents, potentially external web sources (e.g., Wikipedia, research papers)

**Placeholder Questions:**
*   How will the agent prioritize and select relevant information from diverse sources?
*   What mechanisms will ensure accurate citation and attribution?
*   How will the system handle conflicting information from different sources?
*   What is the strategy for evaluating the quality and comprehensiveness of the generated research summaries?

## General Technology Stack & Concepts:

*   **UI:** Gradio
*   **Agent Orchestration:** LangGraph
*   **Database:** Convex DB (for hybrid search, knowledge graph, and persistence)
*   **LLMs:** Hugging Face models (for RAG, Q&A, summarization)
*   **Retrieval:** Hybrid search (vector embeddings + keyword indexing), RAG
*   **Data Ingestion:** PDF parsers, audio transcription, OCR (from Screenpipe)

## Enterprise Knowledge Data:

*   **Data Collection & Processing:** PDF, docs, Wikipedia, Slack, Google Drive (extensible), WhatsApp, messaging channels.
*   **Indexing:** Data Ingestion -> Original doc -> Convert to chunks -> Generate Q/A pair from each chunk -> Index QA embeddings in a vector DB -> Index doc to keyword indexing -> Wrap inside Convex function.

## Runtime Flow:

1.  **User Interaction:** User loads web app (Gradio), uploads a document or provides a query (text/audio).
2.  **Agent Processing:**
    *   **Query Classification/Routing:** Determines the intent of the user's query.
    *   **Retrieval:** Hybrid search on Q&A embeddings (returns parent documents/code).
    *   **Reranking:** Reranks retrieved results for optimal relevance.
    *   **LLM Response:** Generates a response based on the reranked context.
3.  **MCP Server Interaction (for advanced use cases):
**    *   Client-side business logic invokes MCP server.
    *   MCP server returns a list of tools.
    *   LLM selects and executes appropriate tools (e.g., `retrieve` function with query embedding).
    *   Convex function returns chunks/context.
    *   Context + prompt -> LLM Call -> Response.

## Milestones:

*   **Phase 1 (Core MVP):** Gradio app where users can upload documents, generate chunks, and indexed chunks are persisted. Prototype an agentic interaction (e.g., "Why is X important in the company handbook?").
*   **Phase 2 (Enhancements):** Implement personalized features, expand data source integrations, refine hybrid search.
*   **Phase 3 (Advanced):** Integrate knowledge graph for richer RAG, explore advanced agentic behaviors.

## Resources:

*   **Helpful Docs:** https://docs.llamaindex.ai/en/stable/examples/tools/mcp/
*   **Automated Custom Support (Ultravox.ai):** https://demo.ultravox.ai/
*   **LangGraph Knowledge Graph Pipeline:** https://www.marktechpost.com/2025/05/15/a-step-by-step-guide-to-build-an-automated-knowledge-graph-pipeline-using-langgraph-and-networkx/

## Existing Repositories:

*   **Main:** https://github.com/TanGentleman/YouTwo
*   **Audio Data:** https://github.com/TanGentleman/limitless-convex-db
*   **Screenpipe (Data Collection):** https://github.com/TanGentleman/screenpipe-python-client
*   **Enterprise Self-Hosting:** https://github.com/tangentleman/kranti-ai
*   **Augmenta (Advanced RAG):** https://github.com/TanGentleman/Augmenta/blob/main/src/chat.py, https://github.com/TanGentleman/Augmenta/blob/main/src/augmenta/rag.py
*   **Original Screenpipe:** https://github.com/mediar-ai/screenpipe/

## Implementation Principles:

*   **Distill:** Convert arbitrary data into distilled documents.
*   **Plan-and-Execute:** Plan/revise a series of defined subtasks, then execute.
*   **Act:** Perform actions based on agentic decisions.
