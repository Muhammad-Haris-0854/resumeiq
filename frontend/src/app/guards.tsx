import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { Loading } from "@/components/shared";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { missingConfig } from "@/lib/env";

function ConfigGate({ children }: { children: ReactNode }) {
  if (missingConfig.length === 0) return <>{children}</>;
  return (
    <div className="mx-auto max-w-2xl px-6 py-20">
      <Alert tone="warning" title="Configuration needed">
        <p>This deployment is missing environment variables: {missingConfig.join(", ")}.</p>
        <p className="mt-2">
          Copy <code className="rounded bg-slate-100 px-1">frontend/.env.example</code> to{" "}
          <code className="rounded bg-slate-100 px-1">.env</code>, add your Supabase project URL and publishable
          key, then restart the dev server.
        </p>
      </Alert>
    </div>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { session, loading, meError, signOut } = useAuth();
  const location = useLocation();

  if (missingConfig.length > 0) return <ConfigGate>{children}</ConfigGate>;
  if (loading) return <Loading label="Checking your session" />;
  if (!session) return <Navigate to="/login" state={{ from: location.pathname }} replace />;

  if (meError) {
    return (
      <div className="mx-auto max-w-lg px-6 py-24">
        <Alert tone="danger" title="We could not load your account">
          <p>{meError.message}</p>
          <p className="mt-2 text-sm">
            This usually means the API is unreachable or your profile row has not been created yet.
          </p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => void signOut()}>
            Sign out
          </Button>
        </Alert>
      </div>
    );
  }

  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { me, meLoading } = useAuth();
  if (meLoading) return <Loading label="Checking permissions" />;
  if (me?.entitlements.role !== "administrator") return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
