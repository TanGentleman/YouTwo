import { query } from "./_generated/server";
import { v } from "convex/values";

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
    
    // Format response
    const formattedEntities = entities.map((entity) => ({
      id: entity._id,
      name: entity.name,
      entityType: entity.entityType,
      observations: entity.observations,
      updatedAt: entity.updatedAt,
    }));
    
    // Create a map of entity IDs to their formatted representation for easier lookups
    const entityMap = Object.fromEntries(
      formattedEntities.map(entity => [entity.id, entity])
    );
    
    // Format relations with actual entity names instead of IDs
    const formattedRelations = relations.map(relation => {
      const fromEntity = entityMap[relation.from];
      const toEntity = entityMap[relation.to];
      
      return {
        id: relation._id,
        from: fromEntity?.name || relation.from,
        to: toEntity?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      };
    });
    
    return {
      entities: formattedEntities,
      relations: formattedRelations,
    };
  },
});

/**
 * Search for nodes based on query
 */
export const searchNodes = query({
  args: {
    query: v.string(),
  },
  handler: async (ctx, args) => {
    if (!args.query || args.query.trim() === '') {
      return {
        entities: [],
        relations: []
      };
    }

    const query = args.query.toLowerCase();
    
    // Find all entities matching the query
    const entities = await ctx.db.query("entities").collect();
    
    const matchingEntities = entities.filter(entity => {
      // Match entity name
      if (entity.name.toLowerCase().includes(query)) {
        return true;
      }
      
      // Match entity type
      if (entity.entityType.toLowerCase().includes(query)) {
        return true;
      }
      
      // Match any observation
      if (entity.observations.some(obs => 
        obs.toLowerCase().includes(query)
      )) {
        return true;
      }
      
      return false;
    });
    
    if (matchingEntities.length === 0) {
      return {
        entities: [],
        relations: []
      };
    }
    
    const matchingEntityIds = new Set(matchingEntities.map(e => e._id));
    
    // Find relations connected to these entities
    const relations = await ctx.db.query("relations").collect();
    const relatedRelations = relations.filter(rel => 
      matchingEntityIds.has(rel.from) || matchingEntityIds.has(rel.to)
    );
    
    // Format the response
    const formattedEntities = matchingEntities.map(entity => ({
      id: entity._id,
      name: entity.name,
      entityType: entity.entityType,
      observations: entity.observations,
      updatedAt: entity.updatedAt,
    }));
    
    // Create a map of entity IDs to their formatted representation for easier lookups
    const entityMap = Object.fromEntries(
      entities.map(entity => [entity._id, {
        id: entity._id,
        name: entity.name,
        entityType: entity.entityType,
      }])
    );
    
    // Format relations with actual entity names instead of IDs
    const formattedRelations = relatedRelations.map(relation => {
      const fromEntity = entityMap[relation.from];
      const toEntity = entityMap[relation.to];
      
      return {
        id: relation._id,
        from: fromEntity?.name || relation.from,
        to: toEntity?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      };
    });
    
    return {
      entities: formattedEntities,
      relations: formattedRelations,
    };
  },
});

/**
 * Retrieve specific nodes by name
 */

// Note: Change this to run a loop over the names
export const openNodes = query({
  args: {
    names: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    if (!args.names || args.names.length === 0) {
      return {
        entities: [],
        relations: []
      };
    }
    
    const nameSet = new Set(args.names);
    
    // Find the requested entities by name
    const allEntities = await ctx.db.query("entities")
      .collect();
    
    const entities = allEntities.filter(entity => nameSet.has(entity.name));
    
    if (entities.length === 0) {
      return {
        entities: [],
        relations: []
      };
    }
    
    // Get IDs of the found entities
    const entityIds = entities.map(e => e._id);
    const entityIdSet = new Set(entityIds);
    
    // Find relations between these entities
    const allRelations = await ctx.db.query("relations")
      .collect();

    const relations = allRelations.filter(relation => 
      entityIdSet.has(relation.from) || entityIdSet.has(relation.to)
    );
    
    // Format the response
    const formattedEntities = entities.map(entity => ({
      id: entity._id,
      name: entity.name,
      entityType: entity.entityType,
      observations: entity.observations,
      updatedAt: entity.updatedAt,
    }));
    
    // Create a map of entity IDs to their formatted representation for easier lookups
    const entityMap = Object.fromEntries(
      entities.map(entity => [entity._id, {
        id: entity._id,
        name: entity.name,
      }])
    );
    
    // Format relations with actual entity names instead of IDs
    const formattedRelations = relations.map(relation => {
      const fromEntity = entityMap[relation.from];
      const toEntity = entityMap[relation.to];
      
      return {
        id: relation._id,
        from: fromEntity?.name || relation.from,
        to: toEntity?.name || relation.to,
        relationType: relation.relationType,
        fromEntityId: relation.from,
        toEntityId: relation.to,
      };
    });
    
    return {
      entities: formattedEntities,
      relations: formattedRelations,
    };
  },
}); 