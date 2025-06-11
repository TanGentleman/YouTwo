/**
 * This file defines the CRUD (Create, Read, Update, Delete) operations
 * for the 'metadata' table in the Convex database.
 */
import { internalQuery, internalMutation } from './_generated/server';
import { v } from 'convex/values';
import { metadataDoc } from './schema';
import { createOperation } from './operations';

// === CREATE ===

/**
 * Creates a metadata document.
 *
 * @param metadata - The metadata document data to insert.
 * @returns The ID of the created document.
 */
export const createMetadata = internalMutation({
  args: {
    metadata: metadataDoc,
  },
  handler: async (ctx, args) => {
    // Check most recent metadata document
    const mostRecentMetadata = await ctx.db.query('metadata').order('desc').first();
    // if (mostRecentMetadata) {
    //   // validation logic here
    // }

    // Insert the metadata document
    const id = await ctx.db.insert('metadata', args.metadata);
    // Log the creation operation
    await createOperation(ctx, {
      operation: 'create',
      table: 'metadata',
      success: true,
      message: `Created metadata document: ${id}`,
    });
    return id;
  },
});

// === READ ===

/**
 * Gets the metadata document.
 * Since there should typically be only one metadata document,
 * this function returns the first one found.
 *
 * @returns The metadata document or null if not found.
 */
export const getMetadata = internalQuery({
  args: {},
  handler: async (ctx) => {
    const metadata = await ctx.db.query('metadata').order('desc').first();
    return metadata;
  },
});

/**
 * Gets a metadata document by its ID.
 *
 * @param id - The ID of the metadata document to retrieve.
 * @returns The metadata document or null if not found.
 */
export const getMetadataById = internalQuery({
  args: {
    id: v.id('metadata'),
  },
  handler: async (ctx, args) => {
    const metadata = await ctx.db.get(args.id);
    return metadata;
  },
});

// === UPDATE ===

// NOTE: Prefer creating a new metadata document instead of updating the existing one
/**
 * Updates a metadata document.
 *
 * @param id - The ID of the metadata document to update.
 * @param metadata - The new metadata data.
 * @returns The ID of the updated document.
 */
export const updateMetadata = internalMutation({
  args: {
    id: v.id('metadata'),
    metadata: metadataDoc,
  },
  handler: async (ctx, args) => {
    const { id, metadata } = args;

    // Check if the document exists
    const existingMetadata = await ctx.db.get(id);
    if (!existingMetadata) {
      throw new Error(`Metadata with ID ${id} not found for update.`);
    }

    // Update the document
    await ctx.db.patch(id, metadata);

    // Log the update operation
    await createOperation(ctx, {
      operation: 'update',
      table: 'metadata',
      success: true,
      message: `Updated metadata document: ${id}`,
    });

    return id;
  },
});

// /**
// //  * Adds journal IDs to the metadata document.
// //  *
// //  * @param id - The ID of the metadata document to update.
// //  * @param journalIds - The journal IDs to add.
// //  * @returns The ID of the updated document.
// //  */
// export const addJournalIds = internalMutation({
//   args: {
//     id: v.id('metadata'),
//     journalIds: v.array(v.id('journals')),
//   },
//   handler: async (ctx, args) => {

//     // Check if the document exists
//     const existingMetadata = await ctx.db.get(args.id);
//     if (!existingMetadata) {
//       throw new Error(`Metadata with ID ${args.id} not found for update.`);
//     }

//     // Get current journal IDs and add new ones (avoiding duplicates)
//     const currentJournalIds = existingMetadata.journalIds || [];
//     const uniqueJournalIds = [...new Set([...currentJournalIds, ...journalIds])];

//     // Update the document
//     await ctx.db.patch(id, { journalIds: uniqueJournalIds });

//     // Log the update operation
//     await createOperation(ctx, {
//       operation: 'update',
//       table: 'metadata',
//       success: true,
//       message: `Added ${journalIds.length} journal IDs to metadata`,
//     });

//     return id;
//   },
// });

// /**
//  * Adds chunk filenames to the metadata document.
//  *
//  * @param id - The ID of the metadata document to update.
//  * @param chunkFilenames - The chunk filenames to add.
//  * @returns The ID of the updated document.
//  */
// export const addChunkFilenames = internalMutation({
//   args: {
//     id: v.id('metadata'),
//     chunkFilenames: v.array(v.string()),
//   },
//   handler: async (ctx, args) => {
//     const { id, chunkFilenames } = args;

//     // Check if the document exists
//     const existingMetadata = await ctx.db.get(id);
//     if (!existingMetadata) {
//       throw new Error(`Metadata with ID ${id} not found for update.`);
//     }

//     // Get current chunk filenames and add new ones (avoiding duplicates)
//     const currentChunkFilenames = existingMetadata.chunkFilenames || [];
//     const uniqueChunkFilenames = [...new Set([...currentChunkFilenames, ...chunkFilenames])];

//     // Update the document
//     await ctx.db.patch(id, { chunkFilenames: uniqueChunkFilenames });

//     // Log the update operation
//     await createOperation(ctx, {
//       operation: 'update',
//       table: 'metadata',
//       success: true,
//       message: `Added ${chunkFilenames.length} chunk filenames to metadata`,
//     });

//     return id;
//   },
// });

// /**
//  * Updates the time range in the metadata document.
//  *
//  * @param id - The ID of the metadata document to update.
//  * @param startTime - The new start time.
//  * @param endTime - The new end time.
//  * @returns The ID of the updated document.
//  */
// export const updateTimeRange = internalMutation({
//   args: {
//     id: v.id('metadata'),
//     startTime: v.optional(v.number()),
//     endTime: v.optional(v.number()),
//   },
//   handler: async (ctx, args) => {
//     const { id, startTime, endTime } = args;

//     // Check if the document exists
//     const existingMetadata = await ctx.db.get(id);
//     if (!existingMetadata) {
//       throw new Error(`Metadata with ID ${id} not found for update.`);
//     }

//     const updates: {startTime?: number, endTime?: number} = {};
//     if (startTime !== undefined) updates.startTime = startTime;
//     if (endTime !== undefined) updates.endTime = endTime;

//     // Update the document
//     await ctx.db.patch(id, updates);

//     // Log the update operation
//     await createOperation(ctx, {
//       operation: 'update',
//       table: 'metadata',
//       success: true,
//       message: `Updated time range in metadata`,
//     });

//     return id;
//   },
// });

// === DELETE ===

/**
 * Deletes a metadata document.
 *
 * @param id - The ID of the metadata document to delete.
 * @returns True if the document was deleted, false otherwise.
 */
export const deleteMetadata = internalMutation({
  args: {
    id: v.id('metadata'),
  },
  handler: async (ctx, args) => {
    const { id } = args;

    // Check if the document exists
    const existingMetadata = await ctx.db.get(id);
    if (!existingMetadata) {
      console.warn(`WARNING: Metadata with ID ${id} not found for deletion`);
      return false;
    }

    // Delete the document
    await ctx.db.delete(id);

    // Log the deletion operation
    await createOperation(ctx, {
      operation: 'delete',
      table: 'metadata',
      success: true,
      message: `Deleted metadata document`,
    });

    return true;
  },
});
