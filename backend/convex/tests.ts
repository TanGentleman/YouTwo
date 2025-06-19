import { internalAction } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

/**
 * Run a test suite to verify the knowledge graph API
 */
export const runTests = internalAction({
  args: {},
  handler: async (ctx) => {
    const results = {
      passed: 0,
      failed: 0,
      tests: [] as { name: string; passed: boolean; details: any }[]
    };

    function recordTest(name: string, passed: boolean, details: any = null) {
      results.tests.push({
        name,
        passed,
        details
      });
      
      if (passed) {
        results.passed++;
      } else {
        results.failed++;
      }
    }
    
    try {
      // Test 1: Create entities
      const entities = [
        {
          name: "Test_Person",
          entityType: "person",
          observations: ["Test observation 1", "Test observation 2"],
          journalIds: []
        },
        {
          name: "Test_Organization",
          entityType: "organization",
          observations: ["Test company"],
          journalIds: []
        }
      ];
      
      const createEntitiesResult = await ctx.runMutation(internal.entities.createEntities, {
        entities
      });
      
      const allEntitiesCreated = createEntitiesResult.every(result => result.success);
      recordTest("Create entities", allEntitiesCreated, { createEntitiesResult });
      
      // Test 2: Create relations
      const relations = [
        {
          from: "Test_Person",
          to: "Test_Organization",
          relationType: "works_at",
          journalIds: []
        }
      ];
      
      const createRelationsResult = await ctx.runMutation(internal.relations.createRelations, {
        relations
      });
      
      const allRelationsCreated = createRelationsResult.every(result => result.success);
      recordTest("Create relations", allRelationsCreated, { createRelationsResult });
      
      // Test 3: Add observations
      const observations = [
        {
          entityName: "Test_Person",
          contents: ["New test observation"]
        }
      ];
      
      const addObservationsResult = await ctx.runMutation(internal.entities.addObservations, {
        observations
      });
      
      const allObservationsAdded = addObservationsResult.every(result => result.success);
      recordTest("Add observations", allObservationsAdded, { addObservationsResult });
      
      // Test 4: Read graph
      const graph = await ctx.runQuery(internal.knowledge.readGraph, {});
      
      const graphHasEntities = graph.entities && graph.entities.length >= 2;
      const graphHasRelations = graph.relations && graph.relations.length >= 1;
      
      recordTest("Read graph", graphHasEntities && graphHasRelations, { 
        entityCount: graph.entities.length,
        relationCount: graph.relations.length
      });
      
      // Test 5: Search nodes
      const searchResults = await ctx.runQuery(internal.knowledge.searchNodes, {
        query: "test"
      });
      
      const searchFoundEntities = searchResults.entities && searchResults.entities.length > 0;
      recordTest("Search nodes", searchFoundEntities, { 
        entityCount: searchResults.entities.length 
      });
      
      // Test 6: Open nodes by name
      const nodeResults = await ctx.runQuery(internal.knowledge.openNodes, {
        names: ["Test_Person", "Test_Organization"]
      });
      
      const openNodesFound = nodeResults.entities && nodeResults.entities.length === 2;
      recordTest("Open nodes", openNodesFound, { 
        entityCount: nodeResults.entities.length 
      });
      
      // Test 7: Delete observations
      const deletions = [
        {
          entityName: "Test_Person",
          observations: ["New test observation"]
        }
      ];
      
      const deleteObservationsResult = await ctx.runMutation(internal.entities.deleteObservations, {
        deletions
      });
      
      const allObservationsDeleted = deleteObservationsResult.every(result => result.success);
      recordTest("Delete observations", allObservationsDeleted, { deleteObservationsResult });
      
      // Test 8: Delete relations
      const deleteRelationsResult = await ctx.runMutation(internal.relations.deleteRelations, {
        relations: relations.map(r => ({
          from: r.from,
          to: r.to,
          relationType: r.relationType
        }))
      });
      
      const allRelationsDeleted = deleteRelationsResult.every(result => result.success);
      recordTest("Delete relations", allRelationsDeleted, { deleteRelationsResult });
      
      // Test 9: Delete entities
      const deleteEntitiesResult = await ctx.runMutation(internal.entities.deleteEntities, {
        entityNames: ["Test_Person", "Test_Organization"]
      });
      
      const allEntitiesDeleted = deleteEntitiesResult.every(result => result.success);
      recordTest("Delete entities", allEntitiesDeleted, { deleteEntitiesResult });
      
      // Log test completion
      await ctx.runMutation(internal.operations.createOperations, {
        operations: [
          {
            operation: "read",
            table: "entities",
            success: true,
            data: {
              message: `Test suite completed: ${results.passed} passed, ${results.failed} failed`
            }
          }
        ]
      });
      
    } catch (error) {
      await ctx.runMutation(internal.operations.createOperations, {
        operations: [
          {
            operation: "read",
            table: "entities",
            success: false,
            data: {
              error: `Test suite failed with error: ${error}`
            }
          }
        ]
      });
      
      recordTest("Test suite execution", false, { error: String(error) });
    }
    
    return results;
  },
});

/**
 * Run tests for the HTTP API endpoints
 */
export const testHttpEndpoints = internalAction({
  args: {},
  handler: async (ctx) => {
    const results = {
      passed: 0,
      failed: 0,
      tests: [] as { name: string; passed: boolean; details: any }[]
    };

    function recordTest(name: string, passed: boolean, details: any = null) {
      results.tests.push({
        name,
        passed,
        details
      });
      
      if (passed) {
        results.passed++;
      } else {
        results.failed++;
      }
    }

    // Get the deployment URL from environment
    const deploymentUrl = process.env.CONVEX_URL;
    if (!deploymentUrl) {
      return {
        passed: 0,
        failed: 1,
        tests: [{ name: "Setup", passed: false, details: "Failed to get deployment URL. Set CONVEX_URL environment variable." }]
      };
    }

    // Helper function for making HTTP requests to our own deployment
    async function fetchEndpoint(path: string, method: string, body: any = null) {
      const url = `${deploymentUrl}${path}`;
      const headers = { "Content-Type": "application/json" };
      const options: RequestInit = { method, headers };
      
      if (body) {
        options.body = JSON.stringify(body);
      }
      
      try {
        const response = await fetch(url, options);
        const responseData = await response.json();
        return {
          status: response.status,
          data: responseData,
          ok: response.ok
        };
      } catch (error) {
        return {
          status: 0,
          error: String(error),
          ok: false
        };
      }
    }

    try {
      // Setup test data
      const testEntities = [
        {
          name: "HTTP_Test_Person", 
          entityType: "person",
          observations: ["HTTP test observation"]
        },
        {
          name: "HTTP_Test_Organization",
          entityType: "organization",
          observations: ["HTTP test company"]
        }
      ];

      const testRelations = [
        {
          from: "HTTP_Test_Person",
          to: "HTTP_Test_Organization",
          relationType: "works_at"
        }
      ];

      const testObservations = [
        {
          entityName: "HTTP_Test_Person",
          contents: ["Additional HTTP test observation"]
        }
      ];

      // Test 1: Create entities via HTTP
      const createEntitiesResponse = await fetchEndpoint("/entities", "POST", { entities: testEntities });
      recordTest("HTTP Create entities", 
        createEntitiesResponse.ok && 
        createEntitiesResponse.data.every((r: any) => r.success),
        { response: createEntitiesResponse }
      );

      // Test 2: Create relations via HTTP
      const createRelationsResponse = await fetchEndpoint("/relations", "POST", { relations: testRelations });
      recordTest("HTTP Create relations",
        createRelationsResponse.ok && 
        createRelationsResponse.data.every((r: any) => r.success),
        { response: createRelationsResponse }
      );

      // Test 3: Add observations via HTTP
      const addObservationsResponse = await fetchEndpoint("/observations", "POST", { observations: testObservations });
      recordTest("HTTP Add observations",
        addObservationsResponse.ok && 
        addObservationsResponse.data.every((r: any) => r.success),
        { response: addObservationsResponse }
      );

      // Test 4: Read graph via HTTP
      const readGraphResponse = await fetchEndpoint("/graph", "GET");
      recordTest("HTTP Read graph", 
        readGraphResponse.ok && 
        readGraphResponse.data.entities && 
        readGraphResponse.data.entities.some((e: any) => e.name === "HTTP_Test_Person"),
        { response: readGraphResponse }
      );

      // Test 5: Search nodes via HTTP
      const searchResponse = await fetchEndpoint("/search?q=HTTP_Test", "GET");
      recordTest("HTTP Search nodes",
        searchResponse.ok && 
        searchResponse.data.entities && 
        searchResponse.data.entities.length > 0,
        { response: searchResponse }
      );

      // Test 6: Get specific nodes via HTTP
      const nodesResponse = await fetchEndpoint("/nodes?names=HTTP_Test_Person,HTTP_Test_Organization", "GET");
      recordTest("HTTP Get nodes",
        nodesResponse.ok && 
        nodesResponse.data.entities && 
        nodesResponse.data.entities.length === 2,
        { response: nodesResponse }
      );

      // Test 7: Error handling - bad request
      const badRequestResponse = await fetchEndpoint("/entities", "POST", { invalid: "data" });
      recordTest("HTTP Error handling - bad request",
        badRequestResponse.status === 400,
        { response: badRequestResponse }
      );

      // Test 8: Delete observations via HTTP
      const deleteObservationsResponse = await fetchEndpoint("/observations", "DELETE", { 
        deletions: [
          {
            entityName: "HTTP_Test_Person",
            observations: ["Additional HTTP test observation"]
          }
        ]
      });
      recordTest("HTTP Delete observations",
        deleteObservationsResponse.ok && 
        deleteObservationsResponse.data.every((r: any) => r.success),
        { response: deleteObservationsResponse }
      );

      // Test 9: Delete relations via HTTP
      const deleteRelationsResponse = await fetchEndpoint("/relations", "DELETE", { relations: testRelations });
      recordTest("HTTP Delete relations",
        deleteRelationsResponse.ok && 
        deleteRelationsResponse.data.every((r: any) => r.success),
        { response: deleteRelationsResponse }
      );

      // Test 10: Delete entities via HTTP
      const deleteEntitiesResponse = await fetchEndpoint("/entities", "DELETE", { 
        entityNames: ["HTTP_Test_Person", "HTTP_Test_Organization"] 
      });
      recordTest("HTTP Delete entities",
        deleteEntitiesResponse.ok && 
        deleteEntitiesResponse.data.every((r: any) => r.success),
        { response: deleteEntitiesResponse }
      );

      // Log test completion
      await ctx.runMutation(internal.operations.createOperations, {
        operations: [
          {
            operation: "read",
            table: "entities",
            success: true,
            data: {
              message: `HTTP test suite completed: ${results.passed} passed, ${results.failed} failed`
            }
          }
        ]
      });

    } catch (error) {
      await ctx.runMutation(internal.operations.createOperations, {
        operations: [
          {
            operation: "read",
            table: "entities",
            success: false,
            data: {
              error: `HTTP test suite failed with error: ${error}`
            }
          }
        ]
      });
      
      recordTest("HTTP test suite execution", false, { error: String(error) });
    }
    
    return results;
  },
}); 