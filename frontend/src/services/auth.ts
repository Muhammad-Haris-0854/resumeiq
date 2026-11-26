import { supabase, supabaseReady } from "@/lib/supabase";
import { ApiError } from "@/lib/api";

function guard(): void {
  if (!supabaseReady) {
    throw new ApiError("Supabase is not configured. Add VITE_SUPABASE_URL and the publishable key.", {
      code: "NOT_CONFIGURED",
    });
  }
}

export async function signUp(email: string, password: string, fullName: string): Promise<{ needsVerification: boolean }> {
  guard();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { full_name: fullName },
      emailRedirectTo: `${window.location.origin}/dashboard`,
    },
  });
  if (error) throw new ApiError(error.message, { code: "SIGNUP_FAILED" });
  return { needsVerification: !data.session };
}

export async function signIn(email: string, password: string): Promise<void> {
  guard();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw new ApiError(error.message, { code: "SIGNIN_FAILED" });
}

export async function signInWithGoogle(): Promise<void> {
  guard();
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${window.location.origin}/dashboard` },
  });
  if (error) throw new ApiError(error.message, { code: "OAUTH_FAILED" });
}

export async function requestPasswordReset(email: string): Promise<void> {
  guard();
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`,
  });
  if (error) throw new ApiError(error.message, { code: "RESET_FAILED" });
}

export async function updatePassword(password: string): Promise<void> {
  guard();
  const { error } = await supabase.auth.updateUser({ password });
  if (error) throw new ApiError(error.message, { code: "UPDATE_FAILED" });
}

export async function signOut(): Promise<void> {
  if (!supabaseReady) return;
  await supabase.auth.signOut();
}
