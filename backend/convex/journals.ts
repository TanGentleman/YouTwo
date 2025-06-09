import { internalQuery, internalMutation, query } from "./_generated/server";
import { v } from "convex/values";
import { Id } from "./_generated/dataModel";
import { internal } from "./_generated/api";

/**
 * Create a new journal entry
 */
export const createJournal = internalMutation({
  args: {
    title: v.string(),
    markdown: v.string(),
    startTime: v.number(),
    endTime: v.number(),
  },
  handler: async (ctx, args) => {
    // Create the journal entry
    const journalId = await ctx.db.insert("journals", {
      title: args.title,
      markdown: args.markdown,
      startTime: args.startTime,
      endTime: args.endTime,
      embeddingId: null, // Will be populated after embedding is generated
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
      await ctx.db.insert("operations", {
        operation: "create",
        table: "markdownEmbeddings",
        success: false,
        data: {
          error: `Failed to create embedding: ${error}`,
        },
      });
    }
    
    // Update metadata to include this journal
    const metadata = await ctx.db.query("metadata").first();
    
    if (metadata) {
      await ctx.db.patch(metadata._id, {
        journalIds: [...metadata.journalIds, journalId],
        endTime: Math.max(metadata.endTime, args.endTime),
      });
    } else {
      // Create metadata if it doesn't exist
      await ctx.db.insert("metadata", {
        startTime: args.startTime,
        endTime: args.endTime,
        syncedUntil: 0, // Haven't processed any journals yet
        journalIds: [journalId],
      });
    }
    
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
    
    await ctx.db.insert("operations", {
      operation: "update",
      table: "journals",
      success: true,
      data: {
        message: `Journal "${journal.title}" updated`,
      },
    });
    
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
    
    if (!journal) {
      throw new Error("Journal not found");
    }
    
    // Delete embedding if exists
    if (journal.embeddingId) {
      await ctx.db.delete(journal.embeddingId);
    }
    
    // Remove from metadata
    const metadata = await ctx.db.query("metadata").first();
    
    if (metadata) {
      await ctx.db.patch(metadata._id, {
        journalIds: metadata.journalIds.filter(id => id !== args.id),
      });
    }
    
    // Delete the journal
    await ctx.db.delete(args.id);
    
    await ctx.db.insert("operations", {
      operation: "delete",
      table: "journals",
      success: true,
      data: {
        message: `Journal "${journal.title}" deleted`,
      },
    });
    
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
    const journalIds = similarEmbeddings.map(emb => emb.journalId).filter(id => id !== args.journalId);
    const similarJournals = await Promise.all(
      journalIds
        .map(id => ctx.db.get(id))
    );
    
    return similarJournals
      .filter((journal) => journal !== null) // Remove nulls
      .map(journal => ({
        id: journal._id,
        title: journal.title,
        markdown: journal.markdown,
        startTime: journal.startTime,
        endTime: journal.endTime,
        date: new Date(journal.startTime).toLocaleDateString(),
      }));
  },
}); 