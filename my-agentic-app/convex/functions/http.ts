import { http } from "convex/functions";

export async function handleDocumentUpload(document) {
    // Logic to handle document upload and processing
    const result = await http.post("/upload", { document });
    return result.data;
}

export async function handleAudioTranscription(audio) {
    // Logic to handle audio transcription
    const result = await http.post("/transcribe", { audio });
    return result.data;
}

export async function handleResearchQuery(query) {
    // Logic to handle research queries
    const result = await http.post("/research", { query });
    return result.data;
}

export async function handleMeetingSummary(meetingData) {
    // Logic to handle meeting summary generation
    const result = await http.post("/summarize", { meetingData });
    return result.data;
}