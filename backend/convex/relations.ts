import { internalMutation, MutationCtx } from "./_generated/server";
import { v } from "convex/values";
import { Doc, Id } from "./_generated/dataModel";
import { internalCreateOperations } from "./operations";
import { getEntityFromName } from "./entities";
import { internalDeleteKnowledge } from "./knowledge";
import { SimpleOp } from "./operations";

type RelationResult = {
  success: boolean;
  from: string;
  to: string;
  relationType: string;
  reason?: string;
  relationId?: Id<"relations">;
}

const KEEP_EMPTY_KNOWLEDGE = false;

export const createRelationsFromIds = internalMutation({
  args: {
    relations: v.array(v.object({
      from: v.id("entities"),
      to: v.id("entities"),
      relationType: v.string(),
      journalIds: v.optional(v.array(v.id("journals"))),
    })),
  },
  handler: async (ctx, args) => {
    // 1. Insert new relations in batch
    const newRelations = await internalCreateRelations(ctx, {
      relations: args.relations.map(rel => ({
        from: rel.from,
        to: rel.to,
        relationType: rel.relationType,
        journalIds: rel.journalIds,
      })),
    });

    // 2. Update knowledge entries
    await updateKnowledgeWithNewRelations(ctx, {
      relations: newRelations,
    });

    return newRelations;
  },
});

// Internal functions should have side effects to knowledge table!
export const internalCreateRelations = async (ctx: MutationCtx,
  args: 
  {
    relations: Omit<Doc<"relations">, "_id" | "_creationTime">[]
  }) => {
    const operations: SimpleOp[] = [];
    const results: Omit<Doc<"relations">, "_creationTime">[] = [];
    const entityMap = new Map<Id<"entities">, Id<"relations">[]>();
    for (const relation of args.relations) {
      const id = await ctx.db.insert("relations", relation);
      results.push({
        _id: id,
        ...relation,
      });
      // Update entityMap with new relation
      if (!entityMap.has(relation.from)) {
        entityMap.set(relation.from, []);
      }
      entityMap.get(relation.from)?.push(id);
      if (!entityMap.has(relation.to)) {
        entityMap.set(relation.to, []);
      }
      entityMap.get(relation.to)?.push(id);
    }
    
    // Update knowledge with new relations
    for (const [entityId, relationIds] of entityMap.entries()) {
      const knowledge = await ctx.db.query("knowledge").withIndex("by_entity", q => q.eq("entity", entityId)).first();
      if (knowledge === null) {
        await ctx.db.insert("knowledge", {
          entity: entityId,
          relations: relationIds,
          updatedAt: Date.now(),
        });
      }
      else {
        await ctx.db.patch(knowledge._id, {
          relations: [...new Set([...knowledge.relations, ...relationIds])],
        });
      }
    }
    if (entityMap.size > 0) {
      operations.push({
        operation: "create" as const,
        table: "relations" as const,
        success: true,
        message: `Created ${results.length} relations`,
      });
      operations.push({
        operation: "create" as const,
        table: "knowledge" as const,
        success: true,
        message: `Updated ${entityMap.size} knowledge entries`,
      });
      await internalCreateOperations(ctx, { operations });
    }
    return results;
}

export const internalUpdateRelations = async (ctx: MutationCtx, args: {
  relations: { id: Id<"relations">; updates: Partial<Doc<"relations">> }[]
}) => {
  const results: Id<"relations">[] = [];
  for (const relation of args.relations) {
    await ctx.db.patch(relation.id, relation.updates);
    results.push(relation.id);
  }
  const operation = {
    operation: "update" as const,
    table: "relations" as const,
    success: true,
    message: `Updated ${results.length} relations`,
  };
  await internalCreateOperations(ctx, { operations: [operation] });
  return results;
};

export const internalDeleteRelations = async (ctx: MutationCtx,
  args: {
    ids: Id<"relations">[]
  }) => {
    const results: Id<"relations">[] = [];
    for (const id of args.ids) {
      await ctx.db.delete(id);
      results.push(id);
    }
    const operation = {
      operation: "delete" as const,
      table: "relations" as const,
      success: true,
      message: `Deleted ${results.length} relations`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });
    return results;
  }

const updateKnowledgeWithNewRelations = async (ctx: MutationCtx, args: {
  relations: Omit<Doc<"relations">, "_creationTime">[]
}) => {
  const toEntities = new Set<Id<"entities">>();
  const fromEntities = new Set<Id<"entities">>();
  const results: {
    entityId: Id<"entities">,
    knowledgeId: Id<"knowledge">,
    newRelationIds: Id<"relations">[],
  }[] = [];
  
  // Collect all entity IDs involved in the relations
  args.relations.forEach(relation => {
    fromEntities.add(relation.from);
    toEntities.add(relation.to);
  });
  
  // Process "from" entities
  for (const entityId of fromEntities) {
    // Get existing knowledge document or create a new one
    const existingKnowledge = await ctx.db
      .query("knowledge")
      .withIndex("by_entity", (q) => q.eq("entity", entityId))
      .first();
    
    const relationIds = args.relations
      .filter(r => r.from === entityId)
      .map(r => r._id);
    
    if (existingKnowledge) {
      // Update existing knowledge with new relations
      const updatedRelations = [...new Set([...existingKnowledge.relations, ...relationIds])];
      await ctx.db.patch(existingKnowledge._id, {
        relations: updatedRelations,
        updatedAt: Date.now()
      });
      results.push({
        entityId,
        knowledgeId: existingKnowledge._id,
        newRelationIds: relationIds
      });
    }
    else {
      // Create new knowledge document
      const knowledgeId = await ctx.db.insert("knowledge", {
        entity: entityId,
        relations: relationIds,
        updatedAt: Date.now()
      });
      results.push({
        entityId,
        knowledgeId,
        newRelationIds: relationIds
      });
    }
    const operation = {
      operation: "create" as const,
      table: "knowledge" as const,
      success: true,
      message: `Created ${results.length} knowledge entries`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });
  }
  
  // Process "to" entities
  for (const entityId of toEntities) {
    // Skip if already processed as a "from" entity
    if (fromEntities.has(entityId)) continue;
    
    // Get existing knowledge document or create a new one
    const existingKnowledge = await ctx.db
      .query("knowledge")
      .withIndex("by_entity", (q) => q.eq("entity", entityId))
      .first();
    
    const relationIds = args.relations
      .filter(r => r.to === entityId)
      .map(r => r._id);
    
    if (existingKnowledge) {
      // Update existing knowledge with new relations
      const updatedRelations = [...new Set([...existingKnowledge.relations, ...relationIds])];
      await ctx.db.patch(existingKnowledge._id, {
        relations: updatedRelations,
        updatedAt: Date.now()
      });
      results.push({
        entityId,
        knowledgeId: existingKnowledge._id,
        newRelationIds: relationIds
      });
    } else {
      // Create new knowledge document
      const knowledgeId = await ctx.db.insert("knowledge", {
        entity: entityId,
        relations: relationIds,
        updatedAt: Date.now()
      });
      results.push({
        entityId,
        knowledgeId,
        newRelationIds: relationIds
      });
    }
  }
  
  return results;
}

const constructValidRelations = async (ctx: MutationCtx, args: { 
  relations: {
    from: string;
    to: string;
    relationType: string;
    journalIds?: Id<"journals">[];
  }[]
  }) => {
  const invalidResults: RelationResult[] = [];
  const relationsToCreate: Omit<Doc<"relations">, "_id" | "_creationTime">[] = [];

    // 1. Collect unique entity names and fetch them all at once
    const allNames = new Set<string>();
    args.relations.forEach(rel => {
      allNames.add(rel.from);
      allNames.add(rel.to);
    });

    const entitiesByName = new Map();
    for (const name of allNames) {
      const entity = await getEntityFromName(ctx, name);
      if (entity !== null) {
        entitiesByName.set(name, entity);
      }
    }

    // 2. Process each relation and separate valid from invalid
    
    for (const rel of args.relations) {
      const fromEntity = entitiesByName.get(rel.from);
      const toEntity = entitiesByName.get(rel.to);
      
      // Skip if entities don't exist
      if (!fromEntity || !toEntity) {
        invalidResults.push({
          success: false,
          from: rel.from,
          to: rel.to,
          relationType: rel.relationType,
          reason: !fromEntity 
            ? `Source entity "${rel.from}" not found` 
            : `Target entity "${rel.to}" not found`
        });
        continue;
      }
      
      // Check if relation already exists
      const existing = await ctx.db
        .query("relations")
        .withIndex("by_from", q => q.eq("from", fromEntity._id))
        .collect()
        .then(rels => rels.find(r => r.to === toEntity._id && r.relationType === rel.relationType));
      
      if (existing) {
        invalidResults.push({
          success: false,
          from: rel.from,
          to: rel.to,
          relationType: rel.relationType,
          reason: `Relation ${rel.from} -> ${rel.to} already exists with id:(${existing._id})`
        });
        continue;
      }
      
      // Add to valid relations
      relationsToCreate.push({
        from: fromEntity._id,
        to: toEntity._id,
        relationType: rel.relationType,
        journalIds: rel.journalIds,
      });
    }
    return {
      invalidResults,
      relationsToCreate,
    }
  }

/**
 * Create multiple new relations between entities
 */
export const createRelations = internalMutation({
  args: {
    relations: v.array(
      v.object({
        from: v.string(),
        to: v.string(),
        relationType: v.string(),
        journalIds: v.optional(v.array(v.id("journals"))),
      })
    ),
  },
  handler: async (ctx, args) => {
    const results: RelationResult[] = [];
    const { invalidResults, relationsToCreate } = await constructValidRelations(ctx, { relations: args.relations });
    if (invalidResults.length > 0) {
      console.error("Invalid relations:\n", invalidResults);
      return invalidResults;
    }
    const relationPartials = await internalCreateRelations(ctx, { relations: relationsToCreate });
    if (relationPartials.length !== relationsToCreate.length) {
      throw new Error("Failed to create all relations");
    }
    for (let i = 0; i < relationsToCreate.length; i++) {
      const relation = relationsToCreate[i];
      const id = relationPartials[i]._id;
      results.push({
        success: true,
        from: relation.from,
        to: relation.to,
        relationType: relation.relationType,
        relationId: id,
      });
    }

    // await updateKnowledgeWithNewRelations(ctx, { relations: relationPartials });
    return results;
  },
});

const constructValidRelationsToDelete = async (ctx: MutationCtx, args: { 
  relations: {
    from: string;
    to: string;
    relationType: string;
  }[]
  }) => {
  const invalidResults: RelationResult[] = [];
  // Map to track relations by ID for de-duplication
  const relationsMap = new Map<string, Doc<"relations">>();

  // 1. Collect unique entity names and fetch them all at once
  const allNames = new Set<string>();
  args.relations.forEach(rel => {
    allNames.add(rel.from);
    allNames.add(rel.to);
  });

  const entitiesByName = new Map();
  for (const name of allNames) {
    const entity = await getEntityFromName(ctx, name);
    if (entity !== null) {
      entitiesByName.set(name, entity);
    }
  }

  // 2. Process each relation and separate valid from invalid
  for (const rel of args.relations) {
    const fromEntity = entitiesByName.get(rel.from);
    const toEntity = entitiesByName.get(rel.to);
    
    // Skip if entities don't exist
    if (!fromEntity || !toEntity) {
      invalidResults.push({
        success: false,
        from: rel.from,
        to: rel.to,
        relationType: rel.relationType,
        reason: !fromEntity 
          ? `Source entity "${rel.from}" not found` 
          : `Target entity "${rel.to}" not found`
      });
      continue;
    }
    
    // Check if relation exists
    const existing = await ctx.db
      .query("relations")
      .withIndex("by_from", q => q.eq("from", fromEntity._id))
      .collect()
      .then(rels => rels.find(r => r.to === toEntity._id && r.relationType === rel.relationType));
    
    if (existing === undefined) {
      invalidResults.push({
        success: false,
        from: rel.from,
        to: rel.to,
        relationType: rel.relationType,
        reason: `Relation ${rel.from} -> ${rel.to} (${rel.relationType}) not found`
      });
      console.log("Invalid relation: ", rel);
      continue;
    }
    
    // Add to valid relations to delete (de-duplicated)
    const relationId = existing._id.toString();
    if (!relationsMap.has(relationId)) {
      relationsMap.set(relationId, existing);
    }
  }
  
  // Convert map values to array
  return {
    invalidResults,
    relationsToDelete: Array.from(relationsMap.values()),
  }
}

/**
 * Constructs valid relations to delete based on entity IDs
 */
const constructValidRelationsToDeleteById = async (ctx: MutationCtx, args: { 
  relations: {
    from: Id<"entities">;
    to: Id<"entities">;
    relationType: string;
  }[]
}) => {
  const invalidResults: RelationResult[] = [];
  const relationsToDelete: Doc<"relations">[] = [];
  // Map to track relations by ID for de-duplication
  const relationsMap = new Map<string, Doc<"relations">>();

  // Process each relation and check if it exists
  for (const rel of args.relations) {
    // Check if both entities exist
    const fromEntity = await ctx.db.get(rel.from);
    const toEntity = await ctx.db.get(rel.to);
    
    if (!fromEntity || !toEntity) {
      invalidResults.push({
        success: false,
        from: fromEntity ? fromEntity.name : String(rel.from),
        to: toEntity ? toEntity.name : String(rel.to),
        relationType: rel.relationType,
        reason: !fromEntity 
          ? `Source entity ID "${rel.from}" not found` 
          : `Target entity ID "${rel.to}" not found`
      });
      continue;
    }
    
    // Check if relation exists
    const existing = await ctx.db
      .query("relations")
      .withIndex("by_from", q => q.eq("from", rel.from))
      .collect()
      .then(rels => rels.find(r => r.to === rel.to && r.relationType === rel.relationType));
    
    if (existing === undefined) {
      invalidResults.push({
        success: false,
        from: fromEntity.name,
        to: toEntity.name,
        relationType: rel.relationType,
        reason: `Relation ${fromEntity.name} -> ${toEntity.name} (${rel.relationType}) not found`
      });
      continue;
    }
    
    // Add to valid relations to delete (de-duplicated)
    const relationId = existing._id.toString();
    if (!relationsMap.has(relationId)) {
      relationsMap.set(relationId, existing);
    }
  }
  
  return {
    invalidResults,
    relationsToDelete: Array.from(relationsMap.values()),
  };
};

const updateKnowledgeWithDeletedRelations = async (ctx: MutationCtx, args: {
  relations: Doc<"relations">[],
}) => {
  // De-duplicate relations by ID
  const uniqueRelations = Array.from(
    new Map(args.relations.map(rel => [rel._id.toString(), rel])).values()
  );
  
  // Collect all entity IDs involved in the relations
  const entityIds = new Set<Id<"entities">>();
  uniqueRelations.forEach(relation => {
    entityIds.add(relation.from);
    entityIds.add(relation.to);
  });
  console.log("Relations to delete: ", uniqueRelations);
  const relationIds = uniqueRelations.map(rel => rel._id);
  console.log("Relation IDs to delete: ", relationIds);
  
  const knowledgeToUpdate: Array<{id: Id<"knowledge">, relations: Id<"relations">[], entityId: Id<"entities">}> = [];
  const knowledgeToDelete: Id<"knowledge">[] = [];
  
  // Only fetch knowledge entries for affected entities
  for (const entityId of entityIds) {
    const knowledge = await ctx.db
      .query("knowledge")
      .withIndex("by_entity", (q) => q.eq("entity", entityId))
      .first();
      
    if (!knowledge) continue;
    
    // Check if this knowledge entry contains any relations to delete
    const updatedRelations = knowledge.relations.filter(
      relId => !relationIds.includes(relId)
    );
    
    // Log the before and after relation IDs to help diagnose issues
    console.log(`Entity ${entityId} - Before filtering: `, knowledge.relations);
    console.log(`Entity ${entityId} - After filtering: `, updatedRelations);
    
    // Skip if this knowledge entry isn't affected
    if (updatedRelations.length === knowledge.relations.length) {
      continue;
    }
    
    // Handle empty knowledge
    if (updatedRelations.length === 0 && !KEEP_EMPTY_KNOWLEDGE) {
      knowledgeToDelete.push(knowledge._id);
    } else {
      knowledgeToUpdate.push({
        id: knowledge._id,
        relations: updatedRelations,
        entityId: knowledge.entity
      });
    }
  }
  
  // Update knowledge entries
  if (knowledgeToUpdate.length > 0) {
    // Update all knowledge entries
    for (const k of knowledgeToUpdate) {
      await ctx.db.patch(k.id, {
        relations: k.relations,
        updatedAt: Date.now()
      });
    }
    
    const operation = {
      operation: "update" as const,
      table: "knowledge" as const,
      success: true,
      message: `Updated ${knowledgeToUpdate.length} knowledge entries`,
    };
    await internalCreateOperations(ctx, { operations: [operation] });
  }
  
  // Delete empty knowledge entries if needed
  if (knowledgeToDelete.length > 0) {
    await internalDeleteKnowledge(ctx, { ids: knowledgeToDelete });
  }
  
  return { knowledgeToUpdate, knowledgeToDelete };
}

/**
 * Delete specific relations from the graph
 * 
 * @param relations - Array of relation objects with from, to, and relationType
 * @param destroyEmptyKnowledge - Optional. If true, knowledge entries with no relations will be deleted
 * @returns Array of results for each relation deletion request
 */
export const deleteRelations = internalMutation({
  args: {
    relations: v.array(
      v.object({
        from: v.string(), // Source entity name
        to: v.string(), // Target entity name
        relationType: v.string(), // Relationship type
      })
    ),
  },
  handler: async (ctx, args) => {
    const { invalidResults, relationsToDelete } = await constructValidRelationsToDelete(ctx, { relations: args.relations });
    
    if (invalidResults.length > 0) {
      console.error("Invalid relations!!");
      return invalidResults;
    }
    
    if (relationsToDelete.length === 0) {
      return [];
    }
    
    // Get relation IDs for deletion
    const relationIds = Array.from(new Set(relationsToDelete.map(rel => rel._id)));
    
    // Update knowledge entries
    await updateKnowledgeWithDeletedRelations(ctx, { 
      relations: relationsToDelete, 
    });

    // Delete relations
    console.log("Deleting relations: ", relationIds);
    await internalDeleteRelations(ctx, { ids: relationIds });
    
    // Create success results
    const results: RelationResult[] = [];
    for (const rel of args.relations) {
      results.push({
        success: true,
        from: rel.from,
        to: rel.to,
        relationType: rel.relationType,
      });
    }
    
    return results;
  },
}); 

/**
 * Delete specific relations from the graph using entity IDs
 * 
 * @param relations - Array of relation objects with from, to as entity IDs, and relationType
 * @param destroyEmptyKnowledge - Optional. If true, knowledge entries with no relations will be deleted
 * @returns Array of results for each relation deletion request
 */
export const deleteRelationsById = internalMutation({
  args: {
    relations: v.array(
      v.object({
        from: v.id("entities"), // Source entity ID
        to: v.id("entities"), // Target entity ID
        relationType: v.string(), // Relationship type
      })
    ),
  },
  handler: async (ctx, args) => {
    const { invalidResults, relationsToDelete } = await constructValidRelationsToDeleteById(ctx, { 
      relations: args.relations 
    });
    
    if (invalidResults.length > 0) {
      console.error("Invalid relations by ID!!");
      return invalidResults;
    }
    
    if (relationsToDelete.length === 0) {
      return [];
    }
    
    // Get relation IDs for deletion
    const relationIds = relationsToDelete.map(rel => rel._id);
    
    // Update knowledge entries
    await updateKnowledgeWithDeletedRelations(ctx, { 
      relations: relationsToDelete, 
    });

    // Delete relations
    await internalDeleteRelations(ctx, { ids: relationIds });
    
    // Create success results
    const results: RelationResult[] = [];
    for (const rel of args.relations) {
      // Get entity names for the result
      const fromEntity = await ctx.db.get(rel.from);
      const toEntity = await ctx.db.get(rel.to);
      
      results.push({
        success: true,
        from: fromEntity?.name || String(rel.from),
        to: toEntity?.name || String(rel.to),
        relationType: rel.relationType,
      });
    }
    
    return results;
  },
}); 