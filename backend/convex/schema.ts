import { defineSchema, defineTable } from 'convex/server';
import { v } from 'convex/values';

// Journal entries - can be used for extracting knowledge
export const journalsDoc = v.object({
  title: v.string(),
  markdown: v.string(),
  startTime: v.number(),
  endTime: v.number(),
  embeddingId: v.union(v.id('markdownEmbeddings'), v.null()),
  references: v.optional(v.array(v.string())),
});

// Entities are primary nodes in the knowledge graph
export const entityDoc = v.object({
  name: v.string(), // Unique identifier for the entity
  entityType: v.string(), // Type classification (person, organization, event, etc.)
  observations: v.array(v.string()), // Atomic facts about this entity
  updatedAt: v.number(), // Timestamp when entity was last updated
});

// Knowledge maps entities to their relationships
export const knowledgeDoc = v.object({
  entity: v.id('entities'),
  relations: v.array(v.id('relations')),
  updatedAt: v.number(), // Timestamp when entity was last updated
});

// Relations define connections between entities
export const relationDoc = v.object({
  from: v.id('entities'), // Source entity ID
  to: v.id('entities'), // Target entity ID
  relationType: v.string(), // Relationship type in active voice (e.g., "works_at")
});

// Operations log records system actions for debugging and monitoring
export const operationsDoc = v.object({
  operation: v.union(
    v.literal('distill'),
    v.literal('create'),
    v.literal('read'),
    v.literal('update'),
    v.literal('delete'),
  ),
  table: v.union(
    v.literal('journals'),
    v.literal('knowledge'),
    v.literal('entities'),
    v.literal('relations'),
    v.literal('metadata'),
    v.literal('markdownEmbeddings'),
  ),
  success: v.boolean(),
  data: v.object({
    message: v.optional(v.string()),
    error: v.optional(v.string()),
  }),
});

// Metadata stores system-wide information
export const metadataDoc = v.object({
  startTime: v.number(), // Earliest record timestamp
  endTime: v.number(), // Latest record timestamp
  syncedUntil: v.number(), // Timestamp of last knowledge extraction
  journalIds: v.array(v.id('journals')), // List of all journal IDs
});

// Vector embeddings for semantic search
export const markdownEmbeddingDoc = v.object({
  markdown: v.string(), // The text content being embedded
  embedding: v.optional(v.array(v.number())), // Vector representation
  journalId: v.id('journals'), // Reference to the journal entry
});

export default defineSchema({
  // Entity-related tables
  entities: defineTable(entityDoc)
    .index("by_name", ["name"]),
  relations: defineTable(relationDoc)
    .index("by_from", ["from"])
    .index("by_to", ["to"]),
    // .index("by_relation_type", ["relationType"]),
  knowledge: defineTable(knowledgeDoc)
    .index("by_entity", ["entity"])
    .index("by_relations", ["relations"]),
  
  // Journal-related tables
  journals: defineTable(journalsDoc),
  markdownEmbeddings: defineTable(markdownEmbeddingDoc)
    .vectorIndex('byEmbedding', {
      vectorField: 'embedding',
      dimensions: 1536, // OpenAI's embedding size
  }),
  
  // System tables
  metadata: defineTable(metadataDoc),
  operations: defineTable(operationsDoc),
});
