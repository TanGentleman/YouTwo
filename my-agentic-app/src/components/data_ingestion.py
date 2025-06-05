from typing import List, Dict, Any
import os
import PyPDF2
import speech_recognition as sr

def parse_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def parse_text_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read().strip()

def transcribe_audio(file_path: str) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)

def ingest_data(file_path: str) -> Dict[str, Any]:
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.pdf':
        return {"type": "document", "content": parse_pdf(file_path)}
    elif file_extension == '.txt':
        return {"type": "document", "content": parse_text_file(file_path)}
    elif file_extension in ['.wav', '.mp3']:
        return {"type": "audio", "content": transcribe_audio(file_path)}
    else:
        raise ValueError("Unsupported file type")