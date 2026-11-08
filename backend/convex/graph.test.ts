/// <reference types="vite/client" />
import { convexTest } from "convex-test";
import { expect, test } from "vitest";
import schema from "./schema";
import { internal } from "./_generated/api";

const modules = import.meta.glob("./**/*.ts");

const ada = { name: "Ada", entityType: "person", observations: ["Writes Rust"] };
const acme = { name: "Acme", entityType: "organization", observations: [] };
const worksAt = { from: "Ada", to: "Acme", relationType: "works_at" };

async function seed() {
  const t = convexTest(schema, modules);
  await t.mutation(internal.entities.createEntities, { entities: [ada, acme] });
  await t.mutation(internal.relations.createRelations, { relations: [worksAt] });
  return t;
}

test("createEntities rejects a duplicate name", async () => {
  const t = await seed();
  const [result] = await t.mutation(internal.entities.createEntities, {
    entities: [{ name: "Ada", entityType: "person" }],
  });
  expect(result.success).toBe(false);
  const graph = await t.query(internal.knowledge.readGraph, {});
  expect(graph.entities.map((e) => e.name).sort()).toEqual(["Acme", "Ada"]);
});

test("readGraph returns relations by entity name", async () => {
  const t = await seed();
  const graph = await t.query(internal.knowledge.readGraph, {});
  expect(graph.relations).toEqual([worksAt]);
});

test("createRelations rejects unknown entities", async () => {
  const t = await seed();
  const results = await t.mutation(internal.relations.createRelations, {
    relations: [{ from: "Ada", to: "Nobody", relationType: "knows" }],
  });
  expect(results.every((r) => !r.success)).toBe(true);
  expect((await t.query(internal.knowledge.readGraph, {})).relations).toHaveLength(1);
});

test("observations are added without duplicates and deleted by value", async () => {
  const t = await seed();
  await t.mutation(internal.entities.addObservations, {
    observations: [{ entityName: "Ada", contents: ["Writes Rust", "Lives in Paris"] }],
  });
  let [node] = (await t.query(internal.knowledge.openNodes, { names: ["Ada"] })).entities;
  expect(node.observations).toEqual(["Writes Rust", "Lives in Paris"]);

  await t.mutation(internal.entities.deleteObservations, {
    deletions: [{ entityName: "Ada", observations: ["Writes Rust"] }],
  });
  [node] = (await t.query(internal.knowledge.openNodes, { names: ["Ada"] })).entities;
  expect(node.observations).toEqual(["Lives in Paris"]);
});

test("searchNodes matches name, type and observations, case-insensitively", async () => {
  const t = await seed();
  const names = async (query: string) =>
    (await t.query(internal.knowledge.searchNodes, { query })).entities.map((e) => e.name);
  expect(await names("ADA")).toEqual(["Ada"]);
  expect(await names("organization")).toEqual(["Acme"]);
  expect(await names("rust")).toEqual(["Ada"]);
  expect(await names("  ")).toEqual([]);
  const { relations } = await t.query(internal.knowledge.searchNodes, { query: "rust" });
  expect(relations.map((r) => [r.from, r.to])).toEqual([["Ada", "Acme"]]);
});

test("openNodes returns the named nodes and their relations", async () => {
  const t = await seed();
  const result = await t.query(internal.knowledge.openNodes, { names: ["Acme", "Missing"] });
  expect(result.entities.map((e) => e.name)).toEqual(["Acme"]);
  expect(result.relations).toHaveLength(1);
});

test("deleteRelations removes one relation and keeps the entities", async () => {
  const t = await seed();
  const [result] = await t.mutation(internal.relations.deleteRelations, { relations: [worksAt] });
  expect(result.success).toBe(true);
  const graph = await t.query(internal.knowledge.readGraph, {});
  expect(graph.relations).toEqual([]);
  expect(graph.entities).toHaveLength(2);
});

test("deleteEntities also deletes the entity's relations", async () => {
  const t = await seed();
  await t.mutation(internal.entities.deleteEntities, { entityNames: ["Acme"] });
  const graph = await t.query(internal.knowledge.readGraph, {});
  expect(graph.entities.map((e) => e.name)).toEqual(["Ada"]);
  expect(graph.relations).toEqual([]);
});

test("deleteEntities on both ends of a relation", async () => {
  const t = await seed();
  const results = await t.mutation(internal.entities.deleteEntities, { entityNames: ["Ada", "Acme"] });
  expect(results.every((r) => r.success)).toBe(true);
  expect(await t.query(internal.knowledge.readGraph, {})).toEqual({ entities: [], relations: [] });
});

test("entities written with legacy journalIds still read and update", async () => {
  const t = convexTest(schema, modules);
  await t.run((ctx) =>
    ctx.db.insert("entities", { ...ada, updatedAt: 0, journalIds: ["jn79hwrxfznrcgy1xsw1qzb1yd8hvfr2"] }),
  );
  await t.mutation(internal.entities.addObservations, {
    observations: [{ entityName: "Ada", contents: ["Likes tea"] }],
  });
  const graph = await t.query(internal.knowledge.readGraph, {});
  expect(graph.entities[0].observations).toEqual(["Writes Rust", "Likes tea"]);
});
