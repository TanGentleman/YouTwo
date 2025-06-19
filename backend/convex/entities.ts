import { internalMutation, internalQuery, MutationCtx, QueryCtx } from "./_generated/server";
import { v } from "convex/values";
import { internalCreateOperations } from "./operations";
import { Doc, Id } from "./_generated/dataModel";
import { entityDoc } from "./schema";
import { internal } from "./_generated/api";

type EntityResult = {
  success: boolean;
  name: string;
  id?: Id<"entities">;
  reason?: string;
};

export const getEntityFromName = async (ctx: QueryCtx | MutationCtx, name: string): Promise<Doc<"entities"> | null> => {
  return await ctx.db.query("entities")
  .withIndex("by_name", (q) => q.eq("name", name))
  .first();
}

export const getBriefEntities = internalQuery({
  args: {
    limit: v.optional(v.number()),
  },
  returns: v.array(v.object({
    name: v.string(),
    entityType: v.string(),
  })),
  handler: async (ctx, args) => {
    if (args.limit && 1 <= args.limit && args.limit <= 200) {
      return (await ctx.db.query("entities").take(args.limit)).map(entity => ({
        // _id: entity._id,
        name: entity.name,
        entityType: entity.entityType,
      }));
    }
    return (await ctx.db.query("entities").collect()).map(entity => ({
      // _id: entity._id,
      name: entity.name,
      entityType: entity.entityType,
    }));
  },
});

export const internalCreateEntities = async (ctx: MutationCtx, args: {
  entities: Omit<Doc<"entities">, "_id" | "_creationTime" | "updatedAt">[]
}) => {
  const results: EntityResult[] = [];
  for (const entity of args.entities) {
    const id = await ctx.db.insert("entities", {
      name: entity.name,
      entityType: entity.entityType,
      observations: entity.observations ?? undefined,
      journalIds: entity.journalIds ?? undefined,
      updatedAt: Date.now(),
    });
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
    await ctx.db.patch(entity.id, {
      ...entity.updates,
      updatedAt: Date.now(),
    });
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
    entities: v.array(v.object({
      name: v.string(),
      entityType: v.string(),
      observations: v.optional(v.array(v.string())),
      journalIds: v.optional(v.array(v.id("journals"))),
    })),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    const newEntities: Omit<Doc<"entities">, "_id" | "_creationTime" | "updatedAt">[] = [];
    const results: EntityResult[] = [];
    for (const entity of args.entities) {
      // Check if entity with this name already exists
      const existingEntity = await getEntityFromName(ctx, entity.name);
      
      if (existingEntity === null) {
        // Create new entity
        newEntities.push({
          name: entity.name,
          entityType: entity.entityType,
          observations: entity.observations || [],
          journalIds: entity.journalIds || [],
        });
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
    let totalNewObservations = 0;
    
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
        totalNewObservations += newObservations.length;
        results.push({
          success: true,
          name: item.entityName,
        });
      } else {
        results.push({
          success: false,
          name: item.entityName,
          reason: "Entity not found",
        });
      }
    }
    
    console.log(`Added ${totalNewObservations} total observations`);
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
    const relationsToDelete: {
      from: Id<"entities">;
      to: Id<"entities">;
      relationType: string;
    }[] = [];

    for (const name of args.entityNames) {
      // Find the entity
      const entity = await getEntityFromName(ctx, name);

      if (entity === null) {
        results.push({
          success: false,
          name,
          reason: "Entity not found",
        });
        continue;
      }
      entitiesToDelete.push(entity._id);

      const relationsToDeleteById = new Map<Id<"relations">, {
        from: Id<"entities">;
        to: Id<"entities">;
        relationType: string;
      }>();

      // Delete all related relations
      const toRelations = await ctx.db
        .query("relations")
        .withIndex("by_to", (q) => q.eq("to", entity._id))
        .collect();

      const fromRelations = await ctx.db
        .query("relations")
        .withIndex("by_from", (q) => q.eq("from", entity._id))
        .collect();

      toRelations.forEach(relation => {
        if (!relationsToDeleteById.has(relation._id)) {
          relationsToDeleteById.set(relation._id, {
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
          });
        }
      });
      fromRelations.forEach(relation => {
        if (!relationsToDeleteById.has(relation._id)) {
          relationsToDeleteById.set(relation._id, {
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
          });
        }
      });
      relationsToDelete.push(...Array.from(relationsToDeleteById.values()));
      if (relationsToDelete.length !== 0) {
        console.log(`Marked ${relationsToDelete.length} relations to delete for entity ${name}`);
      }

      results.push({
        success: true,
        name,
      });
    }
    if (relationsToDelete.length !== 0) {
      console.log(`Deleting ${relationsToDelete.length} relations`);
      await ctx.runMutation(internal.relations.deleteRelationsById, { relations: relationsToDelete });
    }
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
        console.log(`Removed ${removedCount} observations from ${item.entityName}`);
        results.push({
          success: true,
          name: item.entityName,
          id: entity._id,
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
 * Update entities
 */
export const addEntityUpdates = internalMutation({
  args: {
    entities: v.array(v.object({
      id: v.id("entities"),
      newObservations: v.optional(v.array(v.string())),
      newJournalIds: v.optional(v.array(v.id("journals"))),
    })),
  },
  handler: async (ctx, args): Promise<EntityResult[]> => {
    // Group updates by entity ID to combine duplicates
    const results: EntityResult[] = [];
    const updatesMap = new Map<Id<"entities">, {observations: string[], journalIds: Id<"journals">[]}>();
    const entityUpdates: {id: Id<"entities">, updates: {observations: string[], journalIds: Id<"journals">[]}}[] = [];
    for (const entity of args.entities) {
      if (!updatesMap.has(entity.id)) {
        updatesMap.set(entity.id, {
          observations: [],
          journalIds: [],
        });
      }
      const current = updatesMap.get(entity.id)!;
      if (entity.newObservations) {
        current.observations.push(...entity.newObservations);
      }
      if (entity.newJournalIds) {
        current.journalIds.push(...entity.newJournalIds);
      }
    }
    for (const [id, updates] of updatesMap.entries()) {
      if (updates.observations.length === 0 && updates.journalIds.length === 0) {
        console.warn(`Updates were empty for entity ${id}`);
        continue;
      }
      const entity = await ctx.db.get(id);
      if (!entity) {
        results.push({
          success: false,
          name: "N/A",
          reason: `Entity ${id} not found`,
        });
        continue;
      }
      console.log(`Updating entity ${entity.name} with ${updates.observations.length} observations and ${updates.journalIds.length} journal IDs`);
      results.push({
        success: true,
        name: entity.name,
        id,
      });
      entityUpdates.push({
        id,
        updates: {
          observations: Array.from(new Set([...entity.observations, ...updates.observations])),
          journalIds: Array.from(new Set([...(entity.journalIds || []), ...updates.journalIds])),
        },
      });

    }
    await internalUpdateEntities(ctx, { entities: entityUpdates });
    return results;
  },
});