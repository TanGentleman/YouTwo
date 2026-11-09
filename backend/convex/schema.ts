import { defineSchema, defineTable } from 'convex/server';
import { v } from 'convex/values';

// Entities are primary nodes in the knowledge graph
export const entityDoc = v.object({
  name: v.string(), // Unique identifier for the entity
  entityType: v.string(), // Type classification (person, organization, event, etc.)
  observations: v.array(v.string()), // Atomic facts about this entity
  updatedAt: v.number(), // Timestamp when entity was last updated,
  journalIds: v.optional(v.array(v.string())), // Legacy, from the removed journals table; unused
});

// Relations define connections between entities
export const relationDoc = v.object({
  from: v.id('entities'), // Source entity ID
  to: v.id('entities'), // Target entity ID
  relationType: v.string(), // Relationship type in active voice (e.g., "works_at")
  journalIds: v.optional(v.array(v.string())), // Legacy, from the removed journals table; unused
});

// Only one knowledge entry per entity
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

  // System tables
  operations: defineTable(operationsDoc)
});
