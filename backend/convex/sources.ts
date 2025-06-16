/**
 * This file defines the CRUD (Create, Read, Update, Delete) operations
 * for the 'sources' table in the Convex database.
 */
import { internalQuery, internalMutation } from './_generated/server';
import { v } from 'convex/values';
import { Doc, Id } from './_generated/dataModel';
import { sourcesDoc } from './schema';
import { paginationOptsValidator } from 'convex/server';
import { internalCreateOperations } from './operations';
import { getOrCreateMetadata } from './metadata';

// Default values for querying
const defaultLimit = 10;

// === CREATE ===
type SourceReturnData = {
  id: Id<"sources">;
  filename: string;
}
/**
 * Creates multiple source documents in a batch.
 *
 * @param sources - An array of source document data to insert.
 * @returns An array of the IDs for the created documents.
 */
export const createSources = internalMutation({
  args: {
    sources: v.array(sourcesDoc),
  },
  handler: async (ctx, args): Promise<SourceReturnData[]> => {
    const createdSourceIds: SourceReturnData[] = [];

    if (args.sources.length === 0) {
      throw new Error("No sources to create");
    }

    const currentMetadata = await getOrCreateMetadata(ctx);

    const existingFilenames = new Set(currentMetadata.sourceInfo?.map(info => info.filename) ?? []);
    for (const source of args.sources) {
      if (existingFilenames.has(source.filename)) {
        console.warn(`WARNING: Source with filename ${source.filename} already exists`);
        continue;
      }
      existingFilenames.add(source.filename);
      // Insert the source document
      const id = await ctx.db.insert('sources', source);
      createdSourceIds.push({
        id,
        filename: source.filename
      });
    }
    if (createdSourceIds.length === 0) {
      return [];
    }
    const updatedSourceInfo = [...(currentMetadata.sourceInfo || []), ...createdSourceIds.map(source => ({
      convexId: source.id,
      filename: source.filename,
    }))]
    await ctx.db.insert("metadata", {
      startTime: Math.min(currentMetadata.startTime || 0),
      sourceInfo: updatedSourceInfo,
      endTime: Math.max(currentMetadata.endTime || 0),
      journalIds: currentMetadata.journalIds,
    });

    // Log the creation operation
    const operation = {
      operation: 'create' as const,
      table: 'sources' as const,
      success: true,
      message: `Created ${createdSourceIds.length} new sources`,
    }
    await internalCreateOperations(ctx, { operations: [operation] });

    return createdSourceIds;
  },
});

// === READ ===

/**
 * Reads source documents with pagination support.
 *
 * @param paginationOpts - Pagination options including cursor and number of items.
 * @returns Paginated results containing source documents and pagination metadata.
 */
export const paginateSources = internalQuery({
  args: {
    paginationOpts: paginationOptsValidator,
    excludeIds: v.optional(v.array(v.id('sources'))),
  },
  returns: {
    page: v.array(sourcesDoc),
    isDone: v.boolean(),
    continueCursor: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Start building the query
    const paginatedResults = await ctx.db.query('sources')
        .paginate(args.paginationOpts);
    const setOfIds = new Set(args.excludeIds ?? []);
    if (setOfIds.size === 0) {
        return paginatedResults;
    }
    const prunedPage = paginatedResults.page.filter((source) => !setOfIds.has(source._id));
    return {
        page: prunedPage,
        isDone: paginatedResults.isDone,
        continueCursor: paginatedResults.continueCursor,
    }
  },
});

/**
 * Retrieves specific source documents by their filename.
 *
 * @param filenames - An array of source filenames to fetch.
 * @returns An array of found source documents. Logs warnings for missing files.
 */
export const getSourcesByFilename = internalQuery({
  args: {
    filenames: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const sources: Doc<'sources'>[] = [];
    for (const filename of args.filenames) {
      // Use the filename field rather than _id
      const source = await ctx.db
        .query('sources')
        .withIndex('by_filename', (q) => q.eq('filename', filename))
        .first();

      if (source) {
        sources.push(source);
      } else {
        console.warn(`WARNING: Source with filename ${filename} not found`);
      }
    }
    return sources;
  },
});

/** Retrieves specific source documents by their id. */
export const getSourcesById = internalQuery({
  args: {
    ids: v.array(v.id('sources')),
  },
  handler: async (ctx, args) => {
    const sources: Doc<'sources'>[] = [];
    for (const id of args.ids) {
      const source = await ctx.db.get(id);
      if (source) {
        sources.push(source);
      } else {
        console.warn(`WARNING: Source with id ${id} not found`);
      }
    }
    return sources;
  },
});

// === UPDATE ===

/**
 * Updates multiple source documents in a batch.
 *
 * @param updates - An array of objects, each containing the filename of the source to update
 *                  and the new source data.
 * @param abortOnError - If true, the entire operation fails if any single update fails.
 *                       If false (default), skips failed updates and logs warnings.
 * @returns An array of objects, each containing the id and filename of successfully updated documents.
 */
export const updateSources = internalMutation({
  args: {
    updates: v.array(
      v.object({
        id: v.id('sources'), // Use the source filename for updates
        source: sourcesDoc, // The new data for the source
      }),
    ),
    abortOnError: v.optional(v.boolean()), // Default is false/undefined
  },
  handler: async (ctx, args) => {
    const updatedSources: SourceReturnData[] = [];

    for (const update of args.updates) {
      // --- 1. Find the document ---
      const existingSource = await ctx.db
        .query('sources')
        .withIndex('by_id', (q) => q.eq('_id', update.id))
        .first();
      
      if (!existingSource) {
        const errorMsg = `Source with id ${update.id} not found for update.`;
        if (args.abortOnError) {
          throw new Error(errorMsg);
        } else {
          console.warn(`WARNING: ${errorMsg} Skipping.`);
          continue; // Skip this update
        }
      }

      // --- 2. Database Update ---
      await ctx.db.patch(existingSource._id, update.source);
      updatedSources.push({
        id: existingSource._id,
        filename: update.source.filename
      });
    }

    // --- 3. Operation Logging ---
    if (updatedSources.length > 0) {
      const operation = {
        operation: 'update' as const,
        table: 'sources' as const,
        success: true,
        message: `Updated ${updatedSources.length} sources`,
      }
      await internalCreateOperations(ctx, { operations: [operation] });
    }

    return updatedSources;
  },
});

// === DELETE ===

/**
 * Deletes multiple source documents by their filename.
 *
 * @param filenames - An array of filenames of the source documents to delete.
 * @returns An array of objects, each containing the id and filename of successfully deleted documents.
 */
export const deleteSources = internalMutation({
  args: {
    ids: v.array(v.id('sources')),
  },
  handler: async (ctx, args) => {
    const deletedSources: SourceReturnData[] = [];

    for (const id of args.ids) {
      // Find the document by its filename field
      const source = await ctx.db
        .query('sources')
        .withIndex('by_id', (q) => q.eq('_id', id))
        .first();
      
      if (source) {
        await ctx.db.delete(source._id);
        deletedSources.push({
          id: source._id,
          filename: source.filename
        });
      } else {
        console.warn(`WARNING: Source with id ${id} not found for deletion`);
      }
    }

    // Log the deletion operation
    if (deletedSources.length > 0) {
      const operation = {
        operation: 'delete' as const,
        table: 'sources' as const,
        success: true,
        message: `Deleted ${deletedSources.length} sources`,
      }
      await internalCreateOperations(ctx, { operations: [operation] });
    }

    // Return objects with id and filename of successfully deleted documents
    return deletedSources;
  },
});
