/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as embeddings from "../embeddings.js";
import type * as entities from "../entities.js";
import type * as http from "../http.js";
import type * as journals from "../journals.js";
import type * as knowledge from "../knowledge.js";
import type * as metadata from "../metadata.js";
import type * as operations from "../operations.js";
import type * as patches from "../patches.js";
import type * as relations from "../relations.js";
import type * as sources from "../sources.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  embeddings: typeof embeddings;
  entities: typeof entities;
  http: typeof http;
  journals: typeof journals;
  knowledge: typeof knowledge;
  metadata: typeof metadata;
  operations: typeof operations;
  patches: typeof patches;
  relations: typeof relations;
  sources: typeof sources;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
