import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const links = [
  { to: "/features", label: "Features" },
  { to: "/pricing", label: "Pricing" },
];

export function MarketingLayout() {
  const { session } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-line/70 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-navy-900 text-sm font-bold text-white">R</span>
            <span className="text-base font-semibold tracking-tight">ResumeIQ</span>
          </Link>

          <nav className="hidden items-center gap-7 md:flex">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  cn("text-sm font-medium transition-colors", isActive ? "text-ink" : "text-slate-600 hover:text-ink")
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            {session ? (
              <Button size="sm" onClick={() => (window.location.href = "/dashboard")}>
                Open dashboard
              </Button>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={() => (window.location.href = "/login")}>
                  Sign in
                </Button>
                <Button size="sm" onClick={() => (window.location.href = "/signup")}>
                  Get started
                </Button>
              </>
            )}
          </div>

          <button type="button" className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Toggle menu">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {open && (
          <div className="border-t border-line px-5 py-4 md:hidden">
            <div className="flex flex-col gap-3">
              {links.map((link) => (
                <Link key={link.to} to={link.to} className="text-sm font-medium text-slate-700" onClick={() => setOpen(false)}>
                  {link.label}
                </Link>
              ))}
              <Button size="sm" onClick={() => (window.location.href = session ? "/dashboard" : "/signup")}>
                {session ? "Open dashboard" : "Get started free"}
              </Button>
            </div>
          </div>
        )}
      </header>

      <Outlet />

      <footer className="border-t border-line bg-canvas">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-ink">ResumeIQ</p>
            <p className="mt-1 text-xs text-slate-500">Resume intelligence for students, graduates and engineers.</p>
          </div>
          <div className="flex flex-wrap gap-5 text-xs text-slate-500">
            <Link to="/features" className="hover:text-ink">Features</Link>
            <Link to="/pricing" className="hover:text-ink">Pricing</Link>
            <Link to="/login" className="hover:text-ink">Sign in</Link>
            <span>© {new Date().getFullYear()} ResumeIQ</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
