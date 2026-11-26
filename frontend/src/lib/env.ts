/**
 * Environment access with a friendly failure mode.
 *
 * A missing Supabase key must not white-screen the app, so configuration is checked once and
 * surfaced as a banner plus a disabled auth flow.
 */

const raw = {
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL as string | undefined,
  supabaseKey: import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined,
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000",
};

export const env = {
  supabaseUrl: raw.supabaseUrl ?? "",
  supabaseKey: raw.supabaseKey ?? "",
  apiBaseUrl: raw.apiBaseUrl.replace(/\/$/, ""),
};

export const missingConfig: string[] = [
  ...(env.supabaseUrl ? [] : ["VITE_SUPABASE_URL"]),
  ...(env.supabaseKey ? [] : ["VITE_SUPABASE_PUBLISHABLE_KEY"]),
];

export const isConfigured = missingConfig.length === 0;
