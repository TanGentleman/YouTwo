/// <reference types="vite/client" />
import { convexTest } from "convex-test";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import schema from "./schema";

const modules = import.meta.glob("./**/*.ts");

const auth = { Authorization: "Bearer secret" };
const json = (method: string, body: unknown) => ({
  method,
  headers: { ...auth, "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
const get = { headers: auth };

beforeEach(() => vi.stubEnv("YOUTWO_API_TOKEN", "secret"));
afterEach(() => vi.unstubAllEnvs());

test("every route needs the bearer token", async () => {
  const t = convexTest(schema, modules);
  const routes: [string, string][] = [
    ["GET", "/entities"], ["POST", "/entities"], ["DELETE", "/entities"],
    ["POST", "/relations"], ["DELETE", "/relations"],
    ["POST", "/observations"], ["DELETE", "/observations"],
    ["GET", "/graph"], ["GET", "/search?q=a"], ["GET", "/nodes?names=a"],
  ];
  for (const [method, path] of routes) {
    expect((await t.fetch(path, { method })).status, `${method} ${path}`).toBe(401);
    const wrong = { method, headers: { Authorization: "Bearer wrong" } };
    expect((await t.fetch(path, wrong)).status, `${method} ${path}`).toBe(401);
  }
  vi.stubEnv("YOUTWO_API_TOKEN", "");
  expect((await t.fetch("/graph", get)).status).toBe(500);
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

  const graph = await (await t.fetch("/graph", get)).json();
  expect(graph).toEqual({
    entities: [
      { name: "Ada", entityType: "person", observations: ["Lives in Paris"] },
      { name: "Acme", entityType: "organization", observations: [] },
    ],
    relations: [{ from: "Ada", to: "Acme", relationType: "works_at" }],
  });

  const search = await (await t.fetch("/search?q=paris", get)).json();
  expect(search.entities.map((e: { name: string }) => e.name)).toEqual(["Ada"]);

  const nodes = await (await t.fetch("/nodes?names=Acme", get)).json();
  expect(nodes.entities.map((e: { name: string }) => e.name)).toEqual(["Acme"]);

  const entities = await (await t.fetch("/entities", get)).json();
  expect(entities.map((e: { name: string }) => e.name).sort()).toEqual(["Acme", "Ada"]);

  await t.fetch("/relations", json("DELETE", { relations: [{ from: "Ada", to: "Acme", relationType: "works_at" }] }));
  await t.fetch("/entities", json("DELETE", { entityNames: ["Ada", "Acme"] }));
  expect(await (await t.fetch("/graph", get)).json()).toEqual({ entities: [], relations: [] });
});

test("malformed requests get a 400", async () => {
  const t = convexTest(schema, modules);
  expect((await t.fetch("/entities", json("POST", {}))).status).toBe(400);
  expect((await t.fetch("/relations", json("POST", { relations: "x" }))).status).toBe(400);
  expect((await t.fetch("/observations", json("POST", {}))).status).toBe(400);
  expect((await t.fetch("/observations", json("DELETE", { observations: [] }))).status).toBe(400);
  expect((await t.fetch("/entities", json("DELETE", {}))).status).toBe(400);
  expect((await t.fetch("/relations", json("DELETE", {}))).status).toBe(400);
  expect((await t.fetch("/search", get)).status).toBe(400);
  expect((await t.fetch("/nodes", get)).status).toBe(400);
});
