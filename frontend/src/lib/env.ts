/**
 * Environment access with a friendly failure mode.
 *
 * A missing Supabase key or API endpoint must not white-screen the app: configuration is
 * checked once, surfaced as a banner, and affected calls fail with a clear code instead of a
 * network error. That matters for static preview deployments, which intentionally ship
 * without a backend.
 */

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim() ?? "";
const supabaseKey = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined)?.trim() ?? "";
const apiBaseRaw = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ?? "";

/** Dev builds fall back to the local FastAPI server; production builds never guess a host. */
const apiBaseUrl = (apiBaseRaw || (import.meta.env.DEV ? "http://localhost:8000" : "")).replace(/\/$/, "");

export const env = { supabaseUrl, supabaseKey, apiBaseUrl };

/** False for a static UI-only deployment, where the FastAPI service is not reachable. */
export const apiConfigured = apiBaseUrl.length > 0;

export const missingConfig: string[] = [
  ...(env.supabaseUrl ? [] : ["VITE_SUPABASE_URL"]),
  ...(env.supabaseKey ? [] : ["VITE_SUPABASE_PUBLISHABLE_KEY"]),
];

export const isConfigured = missingConfig.length === 0;
