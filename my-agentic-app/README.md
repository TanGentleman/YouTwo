# My Agentic App

## Overview
My Agentic App is a powerful application designed to facilitate intelligent interactions with documents, meetings, and research inquiries. By leveraging Gradio for the frontend, LangGraph for state management and orchestration, and ConvexDB for the backend, this application provides a seamless user experience for document Q&A, personalized meeting assistance, and automated research capabilities.

## Features
- **Intelligent Document Q&A System**: Users can upload documents, which are processed to enable intelligent question and answer interactions.
- **Personalized Meeting Assistant**: The app transcribes meeting audio, extracts key information, and generates tailored summaries for users.
- **Automated Research Agent**: Users can input research questions, and the agent will search a knowledge base, summarize findings, and provide citations.

## Project Structure
```
my-agentic-app
├── src
│   ├── app.py                     # Main entry point of the application
│   ├── agents
│   │   ├── document_qa_agent.py   # Handles document uploads and Q&A processing
│   │   ├── meeting_assistant_agent.py # Manages audio transcription and meeting summaries
│   │   └── research_agent.py       # Searches knowledge base and summarizes findings
│   ├── components
│   │   ├── gradio_ui.py            # Sets up Gradio interface components
│   │   ├── data_ingestion.py       # Handles data ingestion from various sources
│   │   └── retrieval.py            # Implements hybrid search mechanisms
│   └── utils
│       └── __init__.py             # Initializes the utils package
├── convex
│   ├── schema.ts                   # Defines the schema for ConvexDB
│   └── functions
│       ├── http.ts                 # Handles HTTP requests to ConvexDB
│       └── index.ts                # Entry points for backend operations
├── requirements.txt                # Lists project dependencies
└── README.md                       # Documentation for the project
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone https://github.com/TanGentleman/YouTwo
   cd my-agentic-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/app.py
   ```

## Usage Guidelines
- **Document Q&A**: Upload your documents through the Gradio interface and ask questions related to the content.
- **Meeting Assistant**: Upload audio recordings of meetings to receive transcriptions and summaries.
- **Research Agent**: Input your research questions to get summarized findings and citations.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.