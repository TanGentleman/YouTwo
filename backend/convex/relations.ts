import { mutation } from "./_generated/server";
import { v } from "convex/values";
import { Id } from "./_generated/dataModel";

/**
 * Create multiple new relations between entities
 */
export const createRelations = mutation({
  args: {
    relations: v.array(
      v.object({
        from: v.string(), // Source entity name
        to: v.string(), // Target entity name
        relationType: v.string(), // Relationship type in active voice
      })
    ),
  },
  handler: async (ctx, args) => {
    // Collect all unique entity names
    const allNames = new Set<string>();
    args.relations.forEach(rel => {
      allNames.add(rel.from);
      allNames.add(rel.to);
    });

    // Batch fetch all entities
    const entities = await Promise.all(
      Array.from(allNames).map(async name => {
        const entity = await ctx.db
          .query("entities")
          .withIndex("by_name", q => q.eq("name", name))
          .first();
        return { name, entity };
      })
    );

    // Create entity name to document map
    const entityMap = new Map<string, typeof entities[0]["entity"]>();
    entities.forEach(({ name, entity }) => entityMap.set(name, entity));

    // Process relations in parallel
    const results = await Promise.all(
      args.relations.map(async relation => {
        const sourceEntity = entityMap.get(relation.from);
        const targetEntity = entityMap.get(relation.to);

        if (!sourceEntity || !targetEntity) {
          return {
            success: false,
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
            reason: !sourceEntity
              ? `Source entity "${relation.from}" not found`
              : `Target entity "${relation.to}" not found`,
          };
        }

        // Check for duplicate relations
        const existingRelation = (await ctx.db
          .query("relations")
          .withIndex("by_from", q => 
            q
              .eq("from", sourceEntity._id)
          ).collect()).find(
            (rel) => 
              rel.to === targetEntity._id && 
              rel.relationType === relation.relationType
          );

        if (existingRelation) {
          return {
            success: false,
            from: relation.from,
            to: relation.to,
            relationType: relation.relationType,
            reason: "Relation already exists",
          };
        }

        // Create the relation
        const id = await ctx.db.insert("relations", {
          from: sourceEntity._id,
          to: targetEntity._id,
          relationType: relation.relationType,
        });

        // Update knowledge table
        const existingKnowledge = await ctx.db
          .query("knowledge")
          .withIndex("by_entity", q => q.eq("entity", sourceEntity._id))
          .first();

        if (existingKnowledge) {
          await ctx.db.patch(existingKnowledge._id, {
            relations: [...existingKnowledge.relations, id],
            updatedAt: Date.now(),
          });
        } else {
          await ctx.db.insert("knowledge", {
            entity: sourceEntity._id,
            relations: [id],
            updatedAt: Date.now(),
          });
        }

        return {
          success: true,
          id,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
        };
      })
    );

    return results;
  },
});

/**
 * Delete specific relations from the graph
 */
export const deleteRelations = mutation({
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
    const allNames = new Set<string>();
    args.relations.forEach(rel => {
      allNames.add(rel.from);
      allNames.add(rel.to);
    });

    // Batch fetch all entities
    const entities = await Promise.all(
      Array.from(allNames).map(async name => {
        const entity = await ctx.db
          .query("entities")
          .withIndex("by_name", q => q.eq("name", name))
          .first();
        return { name, entity };
      })
    );

    // Create entity name to document map
    const entityMap = new Map<string, typeof entities[0]["entity"]>();
    entities.forEach(({ name, entity }) => entityMap.set(name, entity));

    // Process relations in parallel
    const results = await Promise.all(
      args.relations.map(async relation => {
        const sourceEntity = entityMap.get(relation.from);
        const targetEntity = entityMap.get(relation.to);

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