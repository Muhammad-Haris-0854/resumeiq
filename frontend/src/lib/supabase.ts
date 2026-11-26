import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { env, isConfigured } from "@/lib/env";

/**
 * Single browser client. Only the publishable key is used here; the service-role key never
 * reaches this bundle.
 */
export const supabase: SupabaseClient = createClient(
  env.supabaseUrl || "https://placeholder.supabase.co",
  env.supabaseKey || "placeholder-anon-key",
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: "pkce",
    },
  },
);

export const supabaseReady = isConfigured;

export async function getAccessToken(): Promise<string | null> {
  if (!supabaseReady) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
