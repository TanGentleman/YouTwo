import { internalQuery, internalMutation } from "./_generated/server";
import { v } from "convex/values";
import { Id } from "./_generated/dataModel";
import { internalCreateOperations } from "./operations";
import { journalsDoc } from "./schema";
import { getOrCreateMetadata } from "./metadata";

/**
 * Create a new journal entry
 */
export const createJournal = internalMutation({
  args: journalsDoc,
  handler: async (ctx, args) => {
    // Check most recent metadata document
    const currentMetadata = await getOrCreateMetadata(ctx);

    if (args.sources.length === 0) {
      console.warn("WARNING: No sources provided to journal");
    }
    // Create the journal entry
    const journalId = await ctx.db.insert("journals", {
      title: args.title,
      markdown: args.markdown,
      startTime: args.startTime,
      endTime: args.endTime,
      embeddingId: null, // Will be populated after embedding is generated
      sources: args.sources,
    });
    
    // Log the operation
    await ctx.db.insert("operations", {
      operation: "create",
      table: "journals",
      success: true,
      data: {
        message: `Journal "${args.title}" created`,
      },
    });
    
    // Create embedding asynchronously
    try {
      const embeddingId = await ctx.db.insert("markdownEmbeddings", {
        markdown: args.markdown,
        journalId,
        // embedding will be populated by a separate action
      });
      
      // Update journal with embedding ID
      await ctx.db.patch(journalId, {
        embeddingId,
      });
    } catch (error) {
      const operation = {
        operation: "create" as const,
        table: "markdownEmbeddings" as const,
        success: false,
        message: `Failed to create embedding: ${error}`,
      }
      await internalCreateOperations(ctx, { operations: [operation] });
    }
    
    // Update metadata to include this journal
    
      await ctx.db.insert("metadata", {
        startTime: Math.min(currentMetadata.startTime, args.startTime),
        journalIds: [...(currentMetadata.journalIds || []), journalId],
        endTime: Math.max(currentMetadata.endTime, args.endTime),
        sourceInfo: currentMetadata.sourceInfo,
      });
    
    return journalId;
  },
});

/**
 * Get all journal entries
 */
export const getJournals = internalQuery({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const journals = args.limit ? await ctx.db.query("journals").take(args.limit) : await ctx.db.query("journals").collect();
    
    // Reformat (why?)
    return journals.map(journal => ({
      id: journal._id,
      title: journal.title,
      markdown: journal.markdown,
      startTime: journal.startTime,
      endTime: journal.endTime,
      date: new Date(journal.startTime).toLocaleDateString(),
    }));
  },
});

/**
 * Get a specific journal entry by ID
 */
export const getJournal = internalQuery({
  args: {
    id: v.id("journals"),
  },
  handler: async (ctx, args) => {
    const journal = await ctx.db.get(args.id);
    
    if (!journal) {
      return null;
    }
    
    return {
      id: journal._id,
      title: journal.title,
      markdown: journal.markdown,
      startTime: journal.startTime,
      endTime: journal.endTime,
      date: new Date(journal.startTime).toLocaleDateString(),
    };
  },
});

/**
 * Update a journal entry
 */
export const updateJournal = internalMutation({
  args: {
    id: v.id("journals"),
    title: v.optional(v.string()),
    markdown: v.optional(v.string()),
    startTime: v.optional(v.number()),
    endTime: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const journal = await ctx.db.get(args.id);
    
    if (!journal) {
      throw new Error("Journal not found");
    }
    
    const updates: {
      title?: string;
      markdown?: string;
      startTime?: number;
      endTime?: number;
    } = {};
    let embeddingNeedsUpdate = false;
    
    if (args.title !== undefined) {
      updates.title = args.title;
    }
    
    if (args.markdown !== undefined && args.markdown !== journal.markdown) {
      updates.markdown = args.markdown;
      embeddingNeedsUpdate = true;
    }
    
    if (args.startTime !== undefined) {
      updates.startTime = args.startTime;
    }
    
    if (args.endTime !== undefined) {
      updates.endTime = args.endTime;
    }
    
    // Update the journal entry
    await ctx.db.patch(args.id, updates);
    
    // Update embedding if needed
    if (embeddingNeedsUpdate && journal.embeddingId) {
      await ctx.db.patch(journal.embeddingId, {
        markdown: args.markdown,
        // embedding will be updated by a separate action
      });
    }
    
    const operation = {
      operation: "update" as const,
      table: "journals" as const,
      success: true,
      message: `Journal "${journal.title}" updated`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });
    
    return args.id;
  },
});

/**
 * Delete a journal entry
 */
export const deleteJournal = internalMutation({
  args: {
    id: v.id("journals"),
  },
  handler: async (ctx, args) => {
    const journal = await ctx.db.get(args.id);
    
    if (journal === null) {
      throw new Error("Journal not found");
    }
    
    // Delete embedding if exists
    if (journal.embeddingId) {
      await ctx.db.delete(journal.embeddingId);
    }
    
    // Remove from metadata
    console.log("NOTE: Does not delete journal ID from metadata");
    await ctx.db.delete(args.id);
    
    const operation = {
      operation: "delete" as const,
      table: "journals" as const,
      success: true,
      message: `Journal "${journal.title}" deleted`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });
    
    return args.id;
  },
});

/**
 * Find semantically similar journal entries
 */
export const findSimilarJournals = internalQuery({
  args: {
    journalId: v.id("journals"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const journal = await ctx.db.get(args.journalId);
    
    if (!journal || !journal.embeddingId) {
      return [];
    }
    
    const embedding = await ctx.db.get(journal.embeddingId);
    
    if (!embedding || !embedding.embedding) {
      return [];
    }
    
    const limit = args.limit || 5;
    
    // Find similar embeddings using vector search
    const similarEmbeddings = (await ctx.db
      .query("markdownEmbeddings")
      // .withIndex("byEmbedding", (q) => q.vectorSearch("embedding", embedding.embedding))
      // .filter((q) => q.neq(q.field("_id"), journal.embeddingId))
      .take(limit))
      // remove the current journal from the results
    
    // Get the corresponding journals
    const journalIds: Id<"journals">[] = [];
    for (const emb of similarEmbeddings) {
      if (emb.journalId !== args.journalId) {
        journalIds.push(emb.journalId);
      }
    }

    // const similarJournals: Doc<"journals">[] = [];
    // for (const emb of similarEmbeddings) {
    //   const journal = await ctx.db.get(emb.journalId);
    //   if (journal !== null) {
    //     similarJournals.push(journal);
    //   }
    // }
    return journalIds;
  }
}); 