import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";

import { supabase, supabaseReady } from "@/lib/supabase";
import { accountApi } from "@/services/account";
import * as authService from "@/services/auth";
import type { Me } from "@/types";

interface AuthContextValue {
  session: Session | null;
  loading: boolean;
  me: Me | null;
  meLoading: boolean;
  meError: Error | null;
  signOut: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(supabaseReady);

  useEffect(() => {
    if (!supabaseReady) {
      setLoading(false);
      return;
    }
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session);
      setLoading(false);
    });
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  const meQuery = useQuery({
    queryKey: ["me", session?.user.id ?? "anonymous"],
    queryFn: accountApi.me,
    enabled: Boolean(session) && supabaseReady,
    retry: 1,
    staleTime: 30_000,
  });

  const signOut = useCallback(async () => {
    await authService.signOut();
    queryClient.clear();
    setSession(null);
  }, [queryClient]);

  const refreshMe = useCallback(async () => {
    await meQuery.refetch();
  }, [meQuery]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      me: meQuery.data ?? null,
      meLoading: meQuery.isLoading,
      meError: (meQuery.error as Error | null) ?? null,
      signOut,
      refreshMe,
    }),
    [session, loading, meQuery.data, meQuery.isLoading, meQuery.error, signOut, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
