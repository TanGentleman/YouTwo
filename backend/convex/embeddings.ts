import { internalQuery, internalMutation } from "./_generated/server";
import { v } from "convex/values";
import { internalCreateOperations } from "./operations";

/**
 * Process embeddings for a newly created markdown document
 * Note: This would typically use an external API like OpenAI to generate embeddings
 */
export const generateEmbedding = internalMutation({
  args: {
    markdownEmbeddingId: v.id("markdownEmbeddings"),
  },
  handler: async (ctx, args) => {
    // Get the embedding document
    const doc = await ctx.db.get(args.markdownEmbeddingId);
    
    if (!doc) {
      const operation = {
        operation: "update" as const,
        table: "markdownEmbeddings" as const,
        success: false,
        error: `Embedding document ${args.markdownEmbeddingId} not found`,
      }
      await internalCreateOperations(ctx, { operations: [operation] });
      return null;
    }
    
    try {
      // In a real implementation, you would call an external API like OpenAI here
      // For now, we'll create a simple mock embedding with random values
      const mockEmbedding = createMockEmbedding(doc.markdown);
      
      // Update the document with the embedding
      await ctx.db.patch(args.markdownEmbeddingId, { embedding: mockEmbedding });
      
      const operation = {
        operation: "update" as const,
        table: "markdownEmbeddings" as const,
        success: true,
        message: "Generated embedding for document",
      }
      await internalCreateOperations(ctx, { operations: [operation] });
      
      return args.markdownEmbeddingId;
    } catch (error) {
      const operation = {
        operation: "update" as const,
        table: "markdownEmbeddings" as const,
        success: false,
        error: `Failed to generate embedding: ${error}`,
      }
      await internalCreateOperations(ctx, { operations: [operation] });
      return null;
    }
  },
});

/**
 * Create a mock embedding for a text string
 * This is only for demonstration purposes - in a real implementation, 
 * you would use a proper embedding model from OpenAI, Cohere, etc.
 */
function createMockEmbedding(text: string): number[] {
  // Simple mock: fill with zeros except the first element is the text length mod 1
  const embedding = new Array(1536).fill(0);
  embedding[0] = (text.length % 100) / 100;
  return embedding;
}

/**
 * Get a markdown embedding document by ID (internal)
 */
export const getMarkdownEmbeddingById = internalQuery({
  args: {
    id: v.id("markdownEmbeddings"),
  },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

/**
 * Update an embedding (internal)
 */
export const updateEmbedding = internalMutation({
  args: {
    id: v.id("markdownEmbeddings"),
    embedding: v.array(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.patch(args.id, { embedding: args.embedding });
  },
}); 