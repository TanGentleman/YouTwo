import { internalMutation } from './_generated/server';
import { Doc } from './_generated/dataModel';
import { createOperation } from './operations';

/**
 * Patch to update all source documents:
 * - Set type to "Vectara"
 * - Calculate and set partsCount from parts length
 * - Remove the parts field
 */
export const updateSourcesSchema = internalMutation({
  args: {},
  handler: async (ctx) => {
    const sources = await ctx.db.query("sources").collect();
    let updatedCount = 0;
    
    for (const source of sources) {
      const updates: Partial<Doc<"sources">> = {
        type: "Vectara"
      };
      
      // Set partsCount to parts length if parts exists
      if (source.parts) {
        updates.partsCount = source.parts.length;
      }
      
      // Update the document and remove parts field
      await ctx.db.patch(source._id, updates);
      if (source.parts !== undefined) {
        await ctx.db.patch(source._id, { parts: undefined });
        updatedCount++;
      }
    }
    
    // Log the operation
    await createOperation(ctx, {
      operation: 'update',
      table: 'sources',
      success: true,
      message: `Patched ${updatedCount} source documents: set type to "Vectara", calculated partsCount, removed parts`
    });
    
    return {
      success: true,
      updatedCount,
      message: `Successfully updated ${updatedCount} source documents`
    };
  }
});
