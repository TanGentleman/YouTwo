import { defineApp } from "convex/server";
import { v } from "convex/values";

const app = defineApp({
  env: {
    /** Bearer token for every HTTP route. Unset = every route returns 500. */
    YOUTWO_API_TOKEN: v.optional(v.string()),
  },
});

export default app;
