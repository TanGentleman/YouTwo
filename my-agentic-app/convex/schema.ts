// This file defines the schema for the ConvexDB, specifying the structure of the data to be stored and managed.

export const schema = {
  documents: {
    id: 'string',
    title: 'string',
    content: 'string',
    createdAt: 'date',
    updatedAt: 'date',
  },
  meetings: {
    id: 'string',
    date: 'date',
    participants: 'array',
    transcript: 'string',
    summary: 'string',
    actionItems: 'array',
  },
  researchQueries: {
    id: 'string',
    question: 'string',
    findings: 'string',
    citations: 'array',
    createdAt: 'date',
  },
};