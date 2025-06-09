import { query } from "./_generated/server";
import { v } from "convex/values";
import { Doc, Id } from "./_generated/dataModel";

/**
 * Read the entire knowledge graph
 */
export const readGraph = query({
  args: {},
  handler: async (ctx) => {
    // Get all entities
    const entities = await ctx.db.query("entities").collect();
    
    // Get all relations
    const relations = await ctx.db.query("relations").collect();
    
    // Create a map of entity IDs to entities for relation lookups
    const entityMap = new Map<Id<"entities">, Doc<"entities">>();
    entities.forEach(entity => entityMap.set(entity._id, entity));
    
    return {
      entities: entities.map(entity => ({
        id: entity._id,
        name: entity.name,
        entityType: entity.entityType,
        observations: entity.observations,
        updatedAt: entity.updatedAt,
      })),
      relations: relations.map(relation => ({
        id: relation._id,
        from: entityMap.get(relation.from)?.name || relation.from,
        to: entityMap.get(relation.to)?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      })),
    };
  },
});

/**
 * Search for nodes based on query.
 */
export const searchNodes = query({
  args: { query: v.string() },
  handler: async (ctx, args) => {
    if (!args.query?.trim()) {
      return { entities: [], relations: [] };
    }

    const query = args.query.toLowerCase();
    const allEntities = await ctx.db.query("entities").collect();
    
    const matchingEntities = allEntities.filter(entity => 
      entity.name.toLowerCase().includes(query) ||
      entity.entityType.toLowerCase().includes(query) ||
      entity.observations.some(obs => obs.toLowerCase().includes(query))
    );

    if (matchingEntities.length === 0) {
      return { entities: [], relations: [] };
    }

    const matchingIds = new Set(matchingEntities.map(e => e._id));
    const allRelations = await ctx.db.query("relations").collect();
    
    const relatedRelations = allRelations.filter(rel => 
      matchingIds.has(rel.from) || matchingIds.has(rel.to)
    );

    // Create a map of entity IDs to entities for relation lookups
    const entityMap = new Map<Id<"entities">, Doc<"entities">>();
    allEntities.forEach(entity => entityMap.set(entity._id, entity));

    return {
      entities: matchingEntities.map(entity => ({
        id: entity._id,
        name: entity.name,
        entityType: entity.entityType,
        observations: entity.observations,
        updatedAt: entity.updatedAt,
      })),
      relations: relatedRelations.map(relation => ({
        id: relation._id,
        from: entityMap.get(relation.from)?.name || relation.from,
        to: entityMap.get(relation.to)?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      })),
    };
  },
});

/**
 * Retrieve specific nodes by name
 */
export const openNodes = query({
  args: { names: v.array(v.string()) },
  handler: async (ctx, args) => {
    if (!args.names?.length) {
      return { entities: [], relations: [] };
    }
    
    const nameSet = new Set(args.names);
    const allEntities = await ctx.db.query("entities").collect();
    const entities = allEntities.filter(e => nameSet.has(e.name));
    
    if (entities.length === 0) {
      return { entities: [], relations: [] };
    }

    const entityIds = new Set(entities.map(e => e._id));
    const allRelations = await ctx.db.query("relations").collect();
    
    const relations = allRelations.filter(rel => 
      entityIds.has(rel.from) || entityIds.has(rel.to)
    );

    // Create a map of entity IDs to entities for relation lookups
    const entityMap = new Map<Id<"entities">, Doc<"entities">>();
    allEntities.forEach(entity => entityMap.set(entity._id, entity));

    return {
      entities: entities.map(entity => ({
        id: entity._id,
        name: entity.name,
        entityType: entity.entityType,
        observations: entity.observations,
        updatedAt: entity.updatedAt,
      })),
      relations: relations.map(relation => ({
        id: relation._id,
        from: entityMap.get(relation.from)?.name || relation.from,
        to: entityMap.get(relation.to)?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      })),
    };
  },
});