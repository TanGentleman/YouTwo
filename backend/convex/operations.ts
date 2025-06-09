import { mutation, internalMutation } from "./_generated/server";
import { v } from "convex/values";

/**
 * Log an operation in the operations table
 */
export const logOperation = internalMutation({
  args: {
    operation: v.union(
      v.literal("distill"),
      v.literal("create"),
      v.literal("read"),
      v.literal("update"),
      v.literal("delete")
    ),
    table: v.union(
      v.literal("journals"),
      v.literal("knowledge"),
      v.literal("entities"),
      v.literal("relations"),
      v.literal("metadata"),
      v.literal("markdownEmbeddings")
    ),
    success: v.boolean(),
    message: v.optional(v.string()),
    error: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const operationId = await ctx.db.insert("operations", {
      operation: args.operation,
      table: args.table,
      success: args.success,
      data: {
        message: args.message,
        error: args.error,
      },
    });
    
    return operationId;
  },
});

/**
 * Get recent operations from the operations log
 */
export const getRecentOperations = mutation({
  args: {
    limit: v.optional(v.number()),
    table: v.optional(
      v.union(
        v.literal("journals"),
        v.literal("knowledge"),
        v.literal("entities"),
        v.literal("relations"),
        v.literal("metadata"),
        v.literal("markdownEmbeddings")
      )
    ),
    operation: v.optional(
      v.union(
        v.literal("distill"),
        v.literal("create"),
        v.literal("read"),
        v.literal("update"),
        v.literal("delete")
      )
    ),
  },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    let query = ctx.db.query("operations");
    
    if (args.table) {
      query = query.filter(q => q.eq(q.field("table"), args.table));
    }
    
    if (args.operation) {
      query = query.filter(q => q.eq(q.field("operation"), args.operation));
    }
    
    const operations = await query
      .order("desc")
      .take(limit);
    
    return operations;
  },
}); 