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
    const results = [];

    for (const relation of args.relations) {
      // Find the source and target entities
      const sourceEntity = await ctx.db
        .query("entities")
        .filter((q) => q.eq(q.field("name"), relation.from))
        .first();
      
      const targetEntity = await ctx.db
        .query("entities")
        .filter((q) => q.eq(q.field("name"), relation.to))
        .first();

      if (!sourceEntity || !targetEntity) {
        results.push({
          success: false,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
          reason: !sourceEntity 
            ? `Source entity "${relation.from}" not found`
            : `Target entity "${relation.to}" not found`,
        });
        continue;
      }

      // Check for duplicate relations
      const existingRelation = await ctx.db
        .query("relations")
        .filter((q) => 
          q.and(
            q.eq(q.field("from"), sourceEntity._id),
            q.eq(q.field("to"), targetEntity._id),
            q.eq(q.field("relationType"), relation.relationType)
          )
        )
        .first();

      if (existingRelation) {
        results.push({
          success: false,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
          reason: "Relation already exists",
        });
        continue;
      }

      // Create the relation
      const id = await ctx.db.insert("relations", {
        from: sourceEntity._id,
        to: targetEntity._id,
        relationType: relation.relationType,
      });

      // Update knowledge table with this relation if needed
      const existingKnowledge = await ctx.db
        .query("knowledge")
        .filter((q) => q.eq(q.field("entity"), sourceEntity._id))
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

      results.push({
        success: true,
        id,
        from: relation.from,
        to: relation.to,
        relationType: relation.relationType,
      });
    }

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
    const results = [];

    for (const relation of args.relations) {
      // Find the source and target entities
      const sourceEntity = await ctx.db
        .query("entities")
        .filter((q) => q.eq(q.field("name"), relation.from))
        .first();
      
      const targetEntity = await ctx.db
        .query("entities")
        .filter((q) => q.eq(q.field("name"), relation.to))
        .first();

      if (!sourceEntity || !targetEntity) {
        results.push({
          success: false,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
          reason: "One or both entities not found",
        });
        continue;
      }

      // Find the relation
      const existingRelation = await ctx.db
        .query("relations")
        .filter((q) => 
          q.and(
            q.eq(q.field("from"), sourceEntity._id),
            q.eq(q.field("to"), targetEntity._id),
            q.eq(q.field("relationType"), relation.relationType)
          )
        )
        .first();

      if (!existingRelation) {
        results.push({
          success: false,
          from: relation.from,
          to: relation.to,
          relationType: relation.relationType,
          reason: "Relation not found",
        });
        continue;
      }

      // Remove the relation from any knowledge entries
      const knowledgeEntries = await ctx.db
        .query("knowledge")
        .filter((q) => q.eq(q.field("entity"), sourceEntity._id))
        .collect();

      for (const knowledge of knowledgeEntries) {
        const updatedRelations = knowledge.relations.filter(
          (relId) => relId !== existingRelation._id
        );
        
        await ctx.db.patch(knowledge._id, {
          relations: updatedRelations,
          updatedAt: Date.now(),
        });
      }

      // Delete the relation
      await ctx.db.delete(existingRelation._id);

      results.push({
        success: true,
        from: relation.from,
        to: relation.to,
        relationType: relation.relationType,
      });
    }

    return results;
  },
}); 