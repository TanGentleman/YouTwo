import { internalMutation } from "./_generated/server";
import { v } from "convex/values";
import { createOperation } from "./operations";
import { Id } from "./_generated/dataModel";

type EntityResult = {
  success: boolean;
  id?: Id<"entities">;
  name: string;
  reason?: string;
  addedObservations?: string[];
  relationsRemoved?: number;
  observationsRemoved?: number;
};
/**
 * Create multiple new entities in the knowledge graph
 */
export const createEntities = internalMutation({
  args: {
    entities: v.array(
      v.object({
        name: v.string(),
        entityType: v.string(),
        observations: v.array(v.string()),
      })
    ),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const results: EntityResult[] = [];
    
    for (const entity of args.entities) {
      // Check if entity with this name already exists
      const existingEntity = await ctx.db
        .query("entities")
        .withIndex("by_name", (q) => q.eq("name", entity.name))
        .first();
      
      if (!existingEntity) {
        // Create new entity
        const id = await ctx.db.insert("entities", {
          name: entity.name,
          entityType: entity.entityType,
          observations: entity.observations,
          updatedAt: Date.now(),
        });
        
        results.push({
          success: true,
          id,
          name: entity.name,
        });
      } else {
        results.push({
          success: false,
          name: entity.name,
          reason: "Entity with this name already exists",
        });
      }
    }
    
    return results;
  },
});

/**
 * Add new observations to existing entities
 */
export const addObservations = internalMutation({
  args: {
    observations: v.array(
      v.object({
        entityName: v.string(),
        contents: v.array(v.string()),
      })
    ),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const results: EntityResult[] = [];
    
    for (const item of args.observations) {
      // Find the entity
      const entity = await ctx.db
        .query("entities")
        .withIndex("by_name", (q) => q.eq("name", item.entityName))
        .first();
      
      if (entity) {
        // Get current observations and add new ones (avoiding duplicates)
        const currentObservations = new Set(entity.observations);
        const newObservations: string[] = [];
        
        for (const obs of item.contents) {
          if (!currentObservations.has(obs)) {
            currentObservations.add(obs);
            newObservations.push(obs);
          }
        }
        
        // Update the entity with new observations
        await ctx.db.patch(entity._id, {
          observations: Array.from(currentObservations),
          updatedAt: Date.now(),
        });
        
        results.push({
          success: true,
          name: item.entityName,
          addedObservations: newObservations,
        });
      } else {
        results.push({
          success: false,
          name: item.entityName,
          reason: "Entity not found",
        });
      }
    }
    
    return results;
  },
});

/**
 * Delete entities and their associated relations
 */
export const deleteEntities = internalMutation({
  args: {
    entityNames: v.array(v.string()),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const results: EntityResult[] = [];
    
    for (const name of args.entityNames) {
      // Find the entity
      const entity = await ctx.db
        .query("entities")
        .withIndex("by_name", (q) => q.eq("name", name))
        .first();
      
      if (entity) {
        // Delete all relations where this entity is involved
        const relationsFrom = await ctx.db
          .query("relations")
          .withIndex("by_from", (q) => q.eq("from", entity._id))
          .collect();
        
        const relationsTo = await ctx.db
          .query("relations")
          .withIndex("by_to", (q) => q.eq("to", entity._id))
          .collect();
        
        // Delete all related knowledge entries
        const knowledgeEntries = await ctx.db
          .query("knowledge")
          .withIndex("by_entity", (q) => q.eq("entity", entity._id))
          .collect();
        
        // Delete all relations and knowledge entries
        for (const rel of [...relationsFrom, ...relationsTo]) {
          await ctx.db.delete(rel._id);
        }
        
        for (const knowledge of knowledgeEntries) {
          await ctx.db.delete(knowledge._id);
        }
        
        // Finally delete the entity
        await ctx.db.delete(entity._id);
        
        results.push({
          success: true,
          name,
          relationsRemoved: relationsFrom.length + relationsTo.length,
        });
      } else {
        // Entity doesn't exist, but operation is silent as per spec
        results.push({
          success: false,
          name,
          reason: "Entity not found",
        });
      }
    }
    
    return results;
  },
});

/**
 * Delete specific observations from entities
 */
export const deleteObservations = internalMutation({
  args: {
    deletions: v.array(
      v.object({
        entityName: v.string(),
        observations: v.array(v.string()),
      })
    ),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const results: EntityResult[] = [];
    
    for (const item of args.deletions) {
      // Find the entity
      const entity = await ctx.db
        .query("entities")
        .withIndex("by_name", (q) => q.eq("name", item.entityName))
        .first();
      
      if (entity) {
        // Remove specified observations
        const currentObservations = new Set(entity.observations);
        let removedCount = 0;
        
        for (const obs of item.observations) {
          if (currentObservations.has(obs)) {
            currentObservations.delete(obs);
            removedCount++;
          }
        }
        
        // Update entity with remaining observations
        await ctx.db.patch(entity._id, {
          observations: Array.from(currentObservations),
          updatedAt: Date.now(),
        });
        
        results.push({
          success: true,
          name: item.entityName,
          observationsRemoved: removedCount,
        });
      } else {
        results.push({
          success: false,
          name: item.entityName,
          reason: "Entity not found",
        });
      }
    }
    
    return results;
  },
}); 