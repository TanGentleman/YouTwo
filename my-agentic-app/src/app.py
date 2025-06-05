from gradio import Interface
from agents.document_qa_agent import DocumentQAAgent
from agents.meeting_assistant_agent import MeetingAssistantAgent
from agents.research_agent import ResearchAgent
from components.gradio_ui import create_ui
from components.data_ingestion import ingest_data
from components.retrieval import hybrid_search

def main():
    # Initialize agents
    document_qa_agent = DocumentQAAgent()
    meeting_assistant_agent = MeetingAssistantAgent()
    research_agent = ResearchAgent()

    # Create Gradio UI
    ui = create_ui(document_qa_agent, meeting_assistant_agent, research_agent)

    # Launch the Gradio interface
    ui.launch()

if __name__ == "__main__":
    main()