/// <reference types="vite/client" />
import { convexTest } from "convex-test";
import { expect, test } from "vitest";
import schema from "./schema";

const modules = import.meta.glob("./**/*.ts");

const json = (method: string, body: unknown) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

test("the HTTP API round-trips a small graph", async () => {
  const t = convexTest(schema, modules);
  const created = await t.fetch(
    "/entities",
    json("POST", {
      entities: [
        { name: "Ada", entityType: "person", observations: ["Writes Rust"] },
        { name: "Acme", entityType: "organization" },
      ],
    }),
  );
  expect(created.status).toBe(200);
  expect((await created.json()).every((r: { success: boolean }) => r.success)).toBe(true);

  const related = await t.fetch(
    "/relations",
    json("POST", { relations: [{ from: "Ada", to: "Acme", relationType: "works_at" }] }),
  );
  expect(related.status).toBe(200);

  await t.fetch("/observations", json("POST", { observations: [{ entityName: "Ada", contents: ["Lives in Paris"] }] }));
  await t.fetch("/observations", json("DELETE", { deletions: [{ entityName: "Ada", observations: ["Writes Rust"] }] }));

  const graph = await (await t.fetch("/graph")).json();
  expect(graph).toEqual({
    entities: [
      { name: "Ada", entityType: "person", observations: ["Lives in Paris"] },
      { name: "Acme", entityType: "organization", observations: [] },
    ],
    relations: [{ from: "Ada", to: "Acme", relationType: "works_at" }],
  });

  const search = await (await t.fetch("/search?q=paris")).json();
  expect(search.entities.map((e: { name: string }) => e.name)).toEqual(["Ada"]);

  const nodes = await (await t.fetch("/nodes?names=Acme")).json();
  expect(nodes.entities.map((e: { name: string }) => e.name)).toEqual(["Acme"]);

  const entities = await (await t.fetch("/entities")).json();
  expect(entities.map((e: { name: string }) => e.name).sort()).toEqual(["Acme", "Ada"]);

  await t.fetch("/relations", json("DELETE", { relations: [{ from: "Ada", to: "Acme", relationType: "works_at" }] }));
  await t.fetch("/entities", json("DELETE", { entityNames: ["Ada", "Acme"] }));
  expect(await (await t.fetch("/graph")).json()).toEqual({ entities: [], relations: [] });
});

test("malformed requests get a 400", async () => {
  const t = convexTest(schema, modules);
  expect((await t.fetch("/entities", json("POST", {}))).status).toBe(400);
  expect((await t.fetch("/relations", json("POST", { relations: "x" }))).status).toBe(400);
  expect((await t.fetch("/observations", json("POST", {}))).status).toBe(400);
  expect((await t.fetch("/observations", json("DELETE", { observations: [] }))).status).toBe(400);
  expect((await t.fetch("/entities", json("DELETE", {}))).status).toBe(400);
  expect((await t.fetch("/relations", json("DELETE", {}))).status).toBe(400);
  expect((await t.fetch("/search")).status).toBe(400);
  expect((await t.fetch("/nodes")).status).toBe(400);
});
