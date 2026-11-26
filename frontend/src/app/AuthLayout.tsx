import { CheckCircle2 } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

const points = [
  "Score every dimension, not just keywords",
  "Evidence behind every recommendation",
  "ATS-safe templates that export to PDF",
];

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col justify-center px-6 py-12 sm:px-12">
        <div className="mx-auto w-full max-w-sm">
          <Link to="/" className="mb-8 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-navy-900 text-sm font-bold text-white">R</span>
            <span className="text-base font-semibold tracking-tight">ResumeIQ</span>
          </Link>
          <Outlet />
        </div>
      </div>
      <div className="relative hidden overflow-hidden bg-navy-900 lg:block">
        <div className="absolute inset-0 grid-lines opacity-40" aria-hidden />
        <div className="relative flex h-full flex-col justify-center px-12 text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-300">Resume intelligence</p>
          <h2 className="mt-4 max-w-md text-3xl font-bold leading-tight">
            Know exactly what your resume is missing before a recruiter does.
          </h2>
          <ul className="mt-8 space-y-3 text-sm text-slate-300">
            {points.map((point) => (
              <li key={point} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-400" aria-hidden />
                {point}
              </li>
            ))}
          </ul>
          <p className="mt-10 max-w-sm text-xs leading-relaxed text-slate-400">
            Your documents stay private. Analysis runs on our servers, files are stored in a private bucket, and nothing
            is used to train models.
          </p>
        </div>
      </div>
    </div>
  );
}
