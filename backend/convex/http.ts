import { httpRouter } from "convex/server";
import { internal } from "./_generated/api";
import { httpAction } from "./_generated/server";
const http = httpRouter();

/**
 * Create entities via HTTP API
 */
http.route({
  path: "/entities",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.entities || !Array.isArray(body.entities)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, entities array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    
    const result = await ctx.runMutation(internal.entities.createEntities, { 
      entities: body.entities 
    });
    
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

/**
 * Create relations via HTTP API
 */
http.route({
  path: "/relations",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.relations || !Array.isArray(body.relations)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, relations array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    
    const result = await ctx.runMutation(internal.relations.createRelations, {
      relations: body.relations
    });
    
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

/**
 * Add observations via HTTP API
 */
http.route({
  path: "/observations",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.observations || !Array.isArray(body.observations)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, observations array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    
    const result = await ctx.runMutation(internal.entities.addObservations, {
      observations: body.observations
    });
    
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

/**
 * Read the entire knowledge graph via HTTP API
 */
http.route({
  path: "/graph",
  method: "GET",
  handler: httpAction(async (ctx) => {
    try {
      const result = await ctx.runQuery(internal.knowledge.readGraph, {});
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex query failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Search nodes via HTTP API
 */
http.route({
  path: "/search",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const query = url.searchParams.get("q");
    if (!query) {
      return new Response(JSON.stringify({ error: "No query provided" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    
    try {
      const result = await ctx.runQuery(internal.knowledge.searchNodes, { query });
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex query failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Get specific nodes by name via HTTP API
 */
http.route({
  path: "/nodes",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const namesParam = url.searchParams.get("names") || "";
    const names = namesParam.split(",").filter(Boolean);
    
    if (names.length === 0) {
      return new Response(
        JSON.stringify({ error: "No names provided" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    try {
      const result = await ctx.runQuery(internal.knowledge.openNodes, { names });
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex query failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Delete entities via HTTP API
 */
http.route({
  path: "/entities",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.entityNames || !Array.isArray(body.entityNames)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, entityNames array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    try {
      const result = await ctx.runMutation(internal.entities.deleteEntities, {
        entityNames: body.entityNames
      });
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex mutation failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Delete observations via HTTP API
 */
http.route({
  path: "/observations",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.deletions || !Array.isArray(body.deletions)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, deletions array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    try {
      const result = await ctx.runMutation(internal.entities.deleteObservations, {
        deletions: body.deletions
      });
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex mutation failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Delete relations via HTTP API
 */
http.route({
  path: "/relations",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    
    if (!body.relations || !Array.isArray(body.relations)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, relations array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    try {
      const result = await ctx.runMutation(internal.relations.deleteRelations, {
        relations: body.relations
      });
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex mutation failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Create sources via HTTP API
 */

http.route({
  path: "/sources",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    if (!body.sources || !Array.isArray(body.sources)) {
      return new Response(
        JSON.stringify({ error: "Invalid request body, sources array required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
    try {
      const result = await ctx.runMutation(internal.sources.createSources, { 
        sources: body.sources 
      });
      if (result.length === 0) {
        return new Response(JSON.stringify({ message: "No new vectara ids to create sources for" }), {
          headers: { "Content-Type": "application/json" }
        });
      }
      return new Response(JSON.stringify(result), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Convex mutation failed" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});

/**
 * Get vectara source info
 */
http.route({
  path: "/sources/info",
  method: "GET",
  handler: httpAction(async (ctx) => {
    try {
      const metadata = await ctx.runMutation(internal.metadata.getSafeMetadata);
      if (!metadata) {
        return new Response(JSON.stringify({ error: "No metadata found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        });
      }
      return new Response(JSON.stringify({ sourceInfo: metadata.sourceInfo }), {
        headers: { "Content-Type": "application/json" }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "Failed to get latest metadata" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
});





// Export the HTTP router
export default http; 