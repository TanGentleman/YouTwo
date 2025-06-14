import { internalMutation, MutationCtx } from "./_generated/server";
import { v } from "convex/values";
import { Doc, Id } from "./_generated/dataModel";
import { internalCreateOperations } from "./operations";
import { relationDoc } from "./schema";
import { getEntityFromName } from "./entities";

type RelationResult = {
  success: boolean;
  from: string;
  to: string;
  relationType: string;
  reason?: string;
  relationId?: Id<"relations">;
}

// Internal functions do not have side effects to knowledge table!
export const internalCreateRelations = async (ctx: MutationCtx,
  args: 
  {
    relations: Omit<Doc<"relations">, "_id" | "_creationTime">[]
  }) => {
    const results: Omit<Doc<"relations">, "_creationTime">[] = [];
    for (const relation of args.relations) {
      const id = await ctx.db.insert("relations", relation);
      results.push({
        _id: id,
        ...relation,
      });
    }
    const operation = {
      operation: "create" as const,
      table: "relations" as const,
      success: true,
      message: `Created ${results.length} relations`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });
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
    journalIds: Id<"journals">[];
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
        journalIds: v.array(v.id("journals")),
      })
    ),
  },
  handler: async (ctx, args) => {
    const results: RelationResult[] = [];
    const { invalidResults, relationsToCreate } = await constructValidRelations(ctx, { relations: args.relations });
    if (invalidResults.length > 0) {
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

    await updateKnowledgeWithNewRelations(ctx, { relations: relationPartials });
    return results;
  },
});

/**
 * Delete specific relations from the graph
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
    // Collect all unique entity names
    const allNamesSet = new Set<string>();
    args.relations.forEach(rel => {
      allNamesSet.add(rel.from);
      allNamesSet.add(rel.to);
    });
    const allNames = Array.from(allNamesSet);
    const allEntities: Doc<"entities">[] = [];
    for (const name of allNames) {
      const entity = await getEntityFromName(ctx, name);
      if (entity !== null) {
        allEntities.push(entity);
      }
      else {
        console.warn(`Entity ${name} not found`);
      }
    }


    // Process relations in parallel
    const results = await Promise.all(
      args.relations.map(async relation => {
        const sourceEntity = allEntities.find(e => e.name === relation.from);
        const targetEntity = allEntities.find(e => e.name === relation.to);

        if (!sourceEntity || !targetEntity) {
          return {
            success: false,
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
            reason: "One or both entities not found",
          };
        }

        // Find the relation
        const existingRelation = (await ctx.db
          .query("relations")
          .withIndex("by_from", q => q.eq("from", sourceEntity._id))
          .collect())
          .find(
            (rel) => 
              rel.to === targetEntity._id && 
              rel.relationType === relation.relationType
          );

        if (!existingRelation) {
          return {
            success: false,
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
            reason: "Relation not found",
          };
        }

        // Remove the relation from knowledge entries
        const knowledgeEntries = await ctx.db
          .query("knowledge")
          .withIndex("by_entity", q => q.eq("entity", sourceEntity._id))
          .collect();

        await Promise.all(
          knowledgeEntries.map(async knowledge => {
            const updatedRelations = knowledge.relations.filter(
              relId => relId !== existingRelation._id
            );
            await ctx.db.patch(knowledge._id, {
              relations: updatedRelations,
              updatedAt: Date.now(),
            });
          })
        );

        // Delete the relation
        await ctx.db.delete(existingRelation._id);

        return {
          success: true,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
        };
      })
    );

    return results;
  },
}); 