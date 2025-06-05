from gradio import Interface, inputs, outputs
from agents.document_qa_agent import DocumentQAAgent
from agents.meeting_assistant_agent import MeetingAssistantAgent
from agents.research_agent import ResearchAgent

def create_ui():
    # Initialize agents
    document_qa_agent = DocumentQAAgent()
    meeting_assistant_agent = MeetingAssistantAgent()
    research_agent = ResearchAgent()

    # Define Gradio interface components
    document_input = inputs.File(label="Upload Document")
    audio_input = inputs.Audio(label="Upload Meeting Audio")
    query_input = inputs.Textbox(label="Enter your query")
    
    document_output = outputs.Textbox(label="Q&A Response")
    meeting_output = outputs.Textbox(label="Meeting Summary")
    research_output = outputs.Textbox(label="Research Summary")

    # Define the functions to handle user inputs
    def handle_document_upload(file):
        return document_qa_agent.process_document(file)

    def handle_audio_upload(audio):
        return meeting_assistant_agent.process_audio(audio)

    def handle_query(query):
        return research_agent.answer_query(query)

    # Create the Gradio interface
    interface = Interface(
        fn=[handle_document_upload, handle_audio_upload, handle_query],
        inputs=[document_input, audio_input, query_input],
        outputs=[document_output, meeting_output, research_output],
        title="Agentic Application",
        description="Upload documents, audio, or enter queries for intelligent responses."
    )

    return interface

if __name__ == "__main__":
    create_ui().launch()