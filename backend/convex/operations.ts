import { MutationCtx } from "./_generated/server";
import { internalMutation } from "./_generated/server";
import { v } from "convex/values";
import { Id } from "./_generated/dataModel";
import { operationsDoc } from "./schema";

export async function internalCreateOperations(ctx: MutationCtx, args: {
  operations: {
    operation: "distill" | "create" | "read" | "update" | "delete";
    table: "entities" | "relations" | "knowledge" | "journals" | "markdownEmbeddings" | "metadata" | "sources";
    success: boolean;
    message?: string;
    error?: string;
  }[]
}) {
  const operationIds: Id<"operations">[] = [];
  for (const operation of args.operations) {
    const operationId = await ctx.db.insert("operations", {
      operation: operation.operation,
      table: operation.table,
      success: operation.success,
      data: {
        message: operation.message,
        error: operation.error,
      },
    });
    operationIds.push(operationId);
  }
  return operationIds;
}

/**
 * Log an operation in the operations table
 */
export const createOperations = internalMutation({
  args: {
    operations: v.array(operationsDoc),
  },
  handler: async (ctx, args) => {
    const operationIds: Id<"operations">[] = [];
    for (const operation of args.operations) {
      const operationId = await ctx.db.insert("operations", operation);
      operationIds.push(operationId);
    }
    return operationIds;
  },
});

/**
 * Get recent operations from the operations log
 */
export const getRecentOperations = internalMutation({
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
    let operations = await ctx.db.query("operations")
      .order("desc")
      .take(500);
    
    if (args.table) {
      operations = operations.filter(operation => operation.table === args.table);
    }
    
    if (args.operation) {
      operations = operations.filter(operation => operation.operation === args.operation);
    }
    
    return operations.slice(0, limit);
  },
}); 