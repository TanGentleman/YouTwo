/**
 * This file defines the CRUD (Create, Read, Update, Delete) operations
 * for the 'chunks' table in the Convex database.
 */
import { internalQuery, internalMutation } from './_generated/server';
import { v } from 'convex/values';
import { Doc, Id } from './_generated/dataModel';
import { chunksDoc } from './schema';
import { paginationOptsValidator } from 'convex/server';
import { createOperation } from './operations';
import { getOrCreateMetadata } from './metadata';

// Default values for querying
const defaultLimit = 10;

// === CREATE ===
type ChunkReturnData = {
  id: Id<"chunks">;
  filename: string;
}
/**
 * Creates multiple chunk documents in a batch.
 *
 * @param chunks - An array of chunk document data to insert.
 * @returns An array of the IDs for the created documents.
 */
export const createChunks = internalMutation({
  args: {
    chunks: v.array(chunksDoc),
  },
  handler: async (ctx, args): Promise<ChunkReturnData[]> => {
    const createdChunkIds: ChunkReturnData[] = [];

    if (args.chunks.length === 0) {
      throw new Error("No chunks to create");
    }

    const currentMetadata = await getOrCreateMetadata(ctx);

    const existingFilenames = new Set(currentMetadata.chunkInfo?.map(info => info.filename) ?? []);
    for (const chunk of args.chunks) {
      if (existingFilenames.has(chunk.filename)) {
        console.warn(`WARNING: Chunk with filename ${chunk.filename} already exists`);
        continue;
      }
      existingFilenames.add(chunk.filename);
      // Insert the chunk document
      const id = await ctx.db.insert('chunks', chunk);
      createdChunkIds.push({
        id,
        filename: chunk.filename
      });
    }
    if (createdChunkIds.length === 0) {
      return [];
    }
    const updatedChunkInfo = [...(currentMetadata.chunkInfo || []), ...createdChunkIds.map(chunk => ({
      convexId: chunk.id,
      filename: chunk.filename,
    }))]
    await ctx.db.insert("metadata", {
      startTime: Math.min(currentMetadata.startTime || 0),
      chunkInfo: updatedChunkInfo,
      endTime: Math.max(currentMetadata.endTime || 0),
      syncedUntil: Date.now(),
      journalInfo: currentMetadata.journalInfo,
    });

    // Log the creation operation
    await createOperation(ctx, {
      operation: 'create',
      table: 'chunks',
      success: true,
      message: `Created ${createdChunkIds.length} new chunks`,
    });

    return createdChunkIds;
  },
});

// === READ ===

/**
 * Reads chunk documents with pagination support.
 *
 * @param paginationOpts - Pagination options including cursor and number of items.
 * @returns Paginated results containing chunk documents and pagination metadata.
 */
export const paginateChunks = internalQuery({
  args: {
    paginationOpts: paginationOptsValidator,
    excludeIds: v.optional(v.array(v.id('chunks'))),
  },
  returns: {
    page: v.array(chunksDoc),
    isDone: v.boolean(),
    continueCursor: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Start building the query
    const paginatedResults = await ctx.db.query('chunks')
        .paginate(args.paginationOpts);
    const setOfIds = new Set(args.excludeIds ?? []);
    if (setOfIds.size === 0) {
        return paginatedResults;
    }
    const prunedPage = paginatedResults.page.filter((chunk) => !setOfIds.has(chunk._id));
    return {
        page: prunedPage,
        isDone: paginatedResults.isDone,
        continueCursor: paginatedResults.continueCursor,
    }
  },
});

/**
 * Retrieves specific chunk documents by their filename.
 *
 * @param filenames - An array of chunk filenames to fetch.
 * @returns An array of found chunk documents. Logs warnings for missing files.
 */
export const getChunksByFilename = internalQuery({
  args: {
    filenames: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const chunks: Doc<'chunks'>[] = [];
    for (const filename of args.filenames) {
      // Use the filename field rather than _id
      const chunk = await ctx.db
        .query('chunks')
        .withIndex('by_filename', (q) => q.eq('filename', filename))
        .first();

      if (chunk) {
        chunks.push(chunk);
      } else {
        console.warn(`WARNING: Chunk with filename ${filename} not found`);
      }
    }
    return chunks;
  },
});

/** Retrieves specific chunk documents by their id. */
export const getChunksById = internalQuery({
  args: {
    ids: v.array(v.id('chunks')),
  },
  handler: async (ctx, args) => {
    const chunks: Doc<'chunks'>[] = [];
    for (const id of args.ids) {
      const chunk = await ctx.db.get(id);
      if (chunk) {
        chunks.push(chunk);
      } else {
        console.warn(`WARNING: Chunk with id ${id} not found`);
      }
    }
    return chunks;
  },
});

// === UPDATE ===

/**
 * Updates multiple chunk documents in a batch.
 *
 * @param updates - An array of objects, each containing the filename of the chunk to update
 *                  and the new chunk data.
 * @param abortOnError - If true, the entire operation fails if any single update fails.
 *                       If false (default), skips failed updates and logs warnings.
 * @returns An array of objects, each containing the id and filename of successfully updated documents.
 */
export const updateChunks = internalMutation({
  args: {
    updates: v.array(
      v.object({
        id: v.id('chunks'), // Use the chunk filename for updates
        chunk: chunksDoc, // The new data for the chunk
      }),
    ),
    abortOnError: v.optional(v.boolean()), // Default is false/undefined
  },
  handler: async (ctx, args) => {
    const updatedChunks: ChunkReturnData[] = [];

    for (const update of args.updates) {
      // --- 1. Find the document ---
      const existingChunk = await ctx.db
        .query('chunks')
        .withIndex('by_id', (q) => q.eq('_id', update.id))
        .first();
      
      if (!existingChunk) {
        const errorMsg = `Chunk with id ${update.id} not found for update.`;
        if (args.abortOnError) {
          throw new Error(errorMsg);
        } else {
          console.warn(`WARNING: ${errorMsg} Skipping.`);
          continue; // Skip this update
        }
      }

      // --- 2. Database Update ---
      await ctx.db.patch(existingChunk._id, update.chunk);
      updatedChunks.push({
        id: existingChunk._id,
        filename: update.chunk.filename
      });
    }

    // --- 3. Operation Logging ---
    if (updatedChunks.length > 0) {
      await createOperation(ctx, {
        operation: 'update',
        table: 'chunks',
        success: true,
        message: `Updated ${updatedChunks.length} chunks`,
      });
    }

    return updatedChunks;
  },
});

// === DELETE ===

/**
 * Deletes multiple chunk documents by their filename.
 *
 * @param filenames - An array of filenames of the chunk documents to delete.
 * @returns An array of objects, each containing the id and filename of successfully deleted documents.
 */
export const deleteChunks = internalMutation({
  args: {
    ids: v.array(v.id('chunks')),
  },
  handler: async (ctx, args) => {
    const deletedChunks: ChunkReturnData[] = [];

    for (const id of args.ids) {
      // Find the document by its filename field
      const chunk = await ctx.db
        .query('chunks')
        .withIndex('by_id', (q) => q.eq('_id', id))
        .first();
      
      if (chunk) {
        await ctx.db.delete(chunk._id);
        deletedChunks.push({
          id: chunk._id,
          filename: chunk.filename
        });
      } else {
        console.warn(`WARNING: Chunk with id ${id} not found for deletion`);
      }
    }

    // Log the deletion operation
    if (deletedChunks.length > 0) {
      await createOperation(ctx, {
        operation: 'delete',
        table: 'chunks',
        success: true,
        message: `Deleted ${deletedChunks.length} chunks`,
      });
    }

    // Return objects with id and filename of successfully deleted documents
    return deletedChunks;
  },
});
