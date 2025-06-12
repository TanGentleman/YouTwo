import { defineSchema, defineTable } from 'convex/server';
import { v } from 'convex/values';


const partsList = v.union(v.array(v.string()), v.array(v.number()));
export const sourceInfo = v.object({
  filename: v.string(),
  convexId: v.id('sources'),
  parts: v.optional(partsList),
});

// Distilled journal entries - first layer of memory
export const journalsDoc = v.object({
  title: v.string(),
  markdown: v.string(),
  startTime: v.number(),
  endTime: v.number(),
  embeddingId: v.union(v.id('markdownEmbeddings'), v.null()),
  sources: v.array(sourceInfo),
});

// Entities are primary nodes in the knowledge graph
export const entityDoc = v.object({
  name: v.string(), // Unique identifier for the entity
  entityType: v.string(), // Type classification (person, organization, event, etc.)
  observations: v.array(v.string()), // Atomic facts about this entity
  updatedAt: v.number(), // Timestamp when entity was last updated,
  journalIds: v.array(v.id('journals')), // List of all journal IDs
});

// Relations define connections between entities
export const relationDoc = v.object({
  from: v.id('entities'), // Source entity ID
  to: v.id('entities'), // Target entity ID
  relationType: v.string(), // Relationship type in active voice (e.g., "works_at")
  journalIds: v.array(v.id('journals')), // List of all journal IDs
});


// Knowledge maps entities to their relationships
export const knowledgeDoc = v.object({
  entity: v.id('entities'),
  relations: v.array(v.id('relations')),
  updatedAt: v.number(), // Timestamp when entity was last updated
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
    v.literal('sources'),
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
  sourceInfo: v.array(sourceInfo), // List of all source info
});

// Vector embeddings for semantic search
export const markdownEmbeddingDoc = v.object({
  markdown: v.string(), // The text content being embedded
  embedding: v.optional(v.array(v.number())), // Vector representation
  journalId: v.id('journals'), // Reference to the journal entry
});

// The offset value will be named to partIndex
export const sourcesDoc = v.object({
  filename: v.string(),
  title: v.string(),
  parts: partsList,
});

export default defineSchema({
  entities: defineTable(entityDoc)
    .index("by_name", ["name"]),
  relations: defineTable(relationDoc)
    .index("by_from", ["from"])
    .index("by_to", ["to"]),
    // .index("by_relation_type", ["relationType"]),
  knowledge: defineTable(knowledgeDoc)
    .index("by_entity", ["entity"])
    .index("by_relations", ["relations"]),
  
  journals: defineTable(journalsDoc),
  markdownEmbeddings: defineTable(markdownEmbeddingDoc),
  //   .vectorIndex('by_embedding', {
  //     vectorField: 'embedding',
  //     dimensions: 1536, // OpenAI's embedding size
  // }),
  sources: defineTable(sourcesDoc)
    .index("by_filename", ["filename"]),
  
  // System tables
  metadata: defineTable(metadataDoc),
  operations: defineTable(operationsDoc)
});
