import { action } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

/**
 * Process embeddings for a newly created markdown document
 * Note: This would typically use an external API like OpenAI to generate embeddings
 */
export const generateEmbedding = action({
  args: {
    markdownEmbeddingId: v.id("markdownEmbeddings"),
  },
  handler: async (ctx, args) => {
    // Get the embedding document
    const doc = await ctx.runQuery(internal.embeddings.getMarkdownEmbeddingById, { 
      id: args.markdownEmbeddingId 
    });
    
    if (!doc) {
      await ctx.runMutation(internal.operations.logOperation, {
        operation: "update",
        table: "markdownEmbeddings",
        success: false,
        error: `Embedding document ${args.markdownEmbeddingId} not found`,
      });
      return null;
    }
    
    try {
      // In a real implementation, you would call an external API like OpenAI here
      // For now, we'll create a simple mock embedding with random values
      const mockEmbedding = createMockEmbedding(doc.markdown);
      
      // Update the document with the embedding
      await ctx.runMutation(internal.embeddings.updateEmbedding, {
        id: args.markdownEmbeddingId,
        embedding: mockEmbedding,
      });
      
      await ctx.runMutation(internal.operations.logOperation, {
        operation: "update",
        table: "markdownEmbeddings",
        success: true,
        message: "Generated embedding for document",
      });
      
      return args.markdownEmbeddingId;
    } catch (error) {
      await ctx.runMutation(internal.operations.logOperation, {
        operation: "update",
        table: "markdownEmbeddings",
        success: false,
        error: `Failed to generate embedding: ${error}`,
      });
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
  // In a real implementation, this would be an API call to get embeddings
  // For demo purposes, we'll generate a deterministic pseudo-random embedding based on text
  const seed = hashString(text);
  const embedding = [];
  
  // Generate 1536 dimensions (matching OpenAI's ada-002 embedding size)
  for (let i = 0; i < 1536; i++) {
    // Generate a pseudo-random value between -1 and 1
    const value = (Math.sin(seed * (i + 1) * 0.1) + 1) / 2;
    embedding.push(value);
  }
  
  // Normalize the embedding vector
  const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
  return embedding.map(val => val / magnitude);
}

/**
 * Simple hash function for strings
 */
function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash;
}

/**
 * Get a markdown embedding document by ID (internal)
 */
export const getMarkdownEmbeddingById = action({
  args: {
    id: v.id("markdownEmbeddings"),
  },
  handler: async (ctx, args) => {
    return await ctx.runQuery(async (db) => {
      return await db.get(args.id);
    });
  },
});

/**
 * Update an embedding (internal)
 */
export const updateEmbedding = action({
  args: {
    id: v.id("markdownEmbeddings"),
    embedding: v.array(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.runMutation(async (db) => {
      await db.patch(args.id, { embedding: args.embedding });
      return args.id;
    });
  },
}); 