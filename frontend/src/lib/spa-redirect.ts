/**
 * GitHub Pages has no server-side routing: a hard refresh on /resumeiq/login is a 404.
 * `public/404.html` stores the requested route in sessionStorage and reloads the app shell;
 * this restores it before React Router mounts, so deep links and refreshes behave normally.
 */
const REDIRECT_KEY = "resumeiq:redirect";

export function consumeSpaRedirect(): void {
  if (typeof window === "undefined") return;

  let pending: string | null = null;
  try {
    pending = window.sessionStorage.getItem(REDIRECT_KEY);
    if (pending !== null) window.sessionStorage.removeItem(REDIRECT_KEY);
  } catch {
    return; // storage blocked; the app still opens at the root route
  }
  if (!pending) return;

  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  const path = pending.replace(/^\/+/, "");
  const target = `${base}/${path}`;
  if (window.location.pathname !== target) {
    window.history.replaceState(null, "", target);
  }
}
