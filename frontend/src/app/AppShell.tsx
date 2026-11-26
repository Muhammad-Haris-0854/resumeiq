import {
  BarChart3,
  Briefcase,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn, initials } from "@/lib/utils";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/resumes/upload", label: "Upload resume", icon: Upload },
  { to: "/career", label: "Career domain", icon: Briefcase },
  { to: "/job-match", label: "Job match", icon: BarChart3 },
  { to: "/builder", label: "Resume builder", icon: FileText },
  { to: "/templates", label: "Templates", icon: Sparkles },
  { to: "/subscription", label: "Plan & billing", icon: ShieldCheck },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { me, signOut } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const isAdmin = me?.entitlements.role === "administrator";

  const handleSignOut = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[260px_1fr]">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col bg-navy-900 text-slate-300 transition-transform lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <NavLink to="/dashboard" className="flex items-center gap-2 text-white">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold">R</span>
            <span className="text-base font-semibold tracking-tight">ResumeIQ</span>
          </NavLink>
          <button type="button" className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white",
                )
              }
            >
              <item.icon className="h-4 w-4" aria-hidden />
              {item.label}
            </NavLink>
          ))}
          {isAdmin && (
            <NavLink
              to="/admin"
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white",
                )
              }
            >
              <ShieldCheck className="h-4 w-4" aria-hidden />
              Admin
            </NavLink>
          )}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-brand-600 text-xs font-semibold text-white">
              {initials(me?.profile.full_name ?? me?.profile.email)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{me?.profile.full_name ?? "Your account"}</p>
              <p className="truncate text-xs text-slate-400">{me?.profile.email}</p>
            </div>
            <button type="button" onClick={handleSignOut} aria-label="Sign out" className="text-slate-400 hover:text-white">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {open && <div className="fixed inset-0 z-30 bg-navy-950/50 lg:hidden" onClick={() => setOpen(false)} aria-hidden />}

      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-white/85 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">
              <Menu className="h-5 w-5" />
            </Button>
            <div className="hidden text-sm text-slate-500 sm:block">
              {me ? `${me.entitlements.analyses_remaining} of ${me.entitlements.analysis_quota} analyses left this month` : ""}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {me && (
              <Badge tone={me.entitlements.plan === "free" ? "neutral" : "brand"}>
                {me.entitlements.plan.toUpperCase()} plan
              </Badge>
            )}
            <Button size="sm" onClick={() => navigate("/resumes/upload")}>
              <Upload className="h-4 w-4" />
              New analysis
            </Button>
          </div>
        </header>
        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
