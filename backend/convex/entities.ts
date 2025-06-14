import { internalMutation, MutationCtx, QueryCtx } from "./_generated/server";
import { v } from "convex/values";
import { internalCreateOperations } from "./operations";
import { Doc, Id } from "./_generated/dataModel";
import { entityDoc } from "./schema";
import { internalDeleteRelations } from "./relations";
import { internalDeleteKnowledge } from "./knowledge";

type EntityResult = {
  success: boolean;
  name: string;
  id?: Id<"entities">;
  reason?: string;
  addedObservations?: string[];
  relationsRemoved?: number;
  observationsRemoved?: number;
};

export const getEntityFromName = async (ctx: QueryCtx | MutationCtx, name: string): Promise<Doc<"entities"> | null> => {
  return await ctx.db.query("entities")
  .withIndex("by_name", (q) => q.eq("name", name))
  .first();
}

export const internalCreateEntities = async (ctx: MutationCtx, args: {
  entities: Omit<Doc<"entities">, "_id" | "_creationTime">[]
}) => {
  const results: EntityResult[] = [];
  for (const entity of args.entities) {
    const id = await ctx.db.insert("entities", entity);
    results.push({
      success: true,
      id,
      name: entity.name,
    });
  }
  const operation = {
    operation: "create" as const,
    table: "entities" as const,
    success: true,
    message: `Created ${results.length} entities`,
  }
  await internalCreateOperations(ctx, { operations: [operation] });
  return results;
}

export const internalUpdateEntities = async (ctx: MutationCtx, args: {
  entities: { id: Id<"entities">; updates: Partial<Doc<"entities">> }[]
}) => {
  const results: Id<"entities">[] = [];
  for (const entity of args.entities) {
    await ctx.db.patch(entity.id, entity.updates);
    results.push(entity.id);
  }
  const operation = {
    operation: "update" as const,
    table: "entities" as const,
    success: true,
    message: `Updated ${results.length} entities`,
  };
  await internalCreateOperations(ctx, { operations: [operation] });
  return results;
};

export const internalDeleteEntities = async (ctx: MutationCtx, args: {
  ids: Id<"entities">[]
}) => {
  const results: string[] = [];
  for (const id of args.ids) {
    await ctx.db.delete(id);
    results.push(id);
  }
  const operation = {
    operation: "delete" as const,
    table: "entities" as const,
    success: true,
    message: `Deleted ${results.length} entities`,
  }
  await internalCreateOperations(ctx, { operations: [operation] });
  return results;
}


/**
 * Create multiple new entities in the knowledge graph
 */
export const createEntities = internalMutation({
  args: {
    entities: v.array(entityDoc),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const newEntities: Omit<Doc<"entities">, "_id" | "_creationTime">[] = [];
    const results: EntityResult[] = [];
    for (const entity of args.entities) {
      // Check if entity with this name already exists
      const existingEntity = await getEntityFromName(ctx, entity.name);
      
      if (existingEntity === null) {
        // Create new entity
        newEntities.push(entity);
      } else {
        // Note: In the future, allow same name if different entity types
        results.push({
          success: false,
          name: entity.name,
          reason: `Entity with name ${entity.name} already exists: (${existingEntity._id})`,
        });
      }
    }
    if (newEntities.length === 0) {
      return results;
    }
    const newEntityResults = await internalCreateEntities(ctx, { entities: newEntities });
    return [...results, ...newEntityResults];
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
      const entity = await getEntityFromName(ctx, item.entityName);
      
      if (entity !== null) {
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
    const entitiesToDelete: Id<"entities">[] = [];
    const relationsToDeleteSet = new Set<Id<"relations">>();
    const knowledgeToDelete: Id<"knowledge">[] = [];

    for (const name of args.entityNames) {
      // Find the entity
      const entity = await getEntityFromName(ctx, name);

      if (entity !== null) {
        entitiesToDelete.push(entity._id);

        // Delete all related knowledge entries
        const knowledgeEntry = await ctx.db
          .query("knowledge")
          .withIndex("by_entity", (q) => q.eq("entity", entity._id))
          .unique();

        if (knowledgeEntry === null) {
          continue;
        }
        // Add relations to set to avoid duplicates
        knowledgeEntry.relations.forEach(relationId => relationsToDeleteSet.add(relationId));
        knowledgeToDelete.push(knowledgeEntry._id);
        results.push({
          success: true,
          name,
          relationsRemoved: knowledgeEntry.relations.length,
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

    await internalDeleteKnowledge(ctx, { ids: knowledgeToDelete });
    await internalDeleteRelations(ctx, { ids: Array.from(relationsToDeleteSet) });
    await internalDeleteEntities(ctx, { ids: entitiesToDelete });
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
      const entity = await getEntityFromName(ctx, item.entityName);
      
      if (entity !== null) {
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