import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="font-mono text-xs font-semibold text-brand-600">404</p>
      <h1 className="text-2xl font-bold tracking-tight">That page does not exist</h1>
      <p className="max-w-sm text-sm text-slate-600">
        The link may be outdated, or the resume or report was deleted.
      </p>
      <Link to="/dashboard">
        <Button>Go to dashboard</Button>
      </Link>
    </div>
  );
}
