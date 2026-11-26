import { getAccessToken, supabase, supabaseReady } from "@/lib/supabase";
import { env } from "@/lib/env";

/** Error shape returned by the API, normalised for the UI. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: Record<string, unknown>;
  readonly requestId: string | null;

  constructor(
    message: string,
    options: { code?: string; status?: number; details?: Record<string, unknown>; requestId?: string | null } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.code = options.code ?? "UNKNOWN";
    this.status = options.status ?? 0;
    this.details = options.details ?? {};
    this.requestId = options.requestId ?? null;
  }
}

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

interface RequestOptions {
  method?: Method;
  body?: unknown;
  formData?: FormData;
  auth?: boolean;
  signal?: AbortSignal;
}

let refreshInFlight: Promise<void> | null = null;

async function ensureFreshToken(): Promise<string | null> {
  const token = await getAccessToken();
  if (token) return token;
  if (!supabaseReady) return null;
  if (!refreshInFlight) {
    refreshInFlight = supabase.auth
      .refreshSession()
      .then(() => undefined)
      .catch(() => undefined)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  await refreshInFlight;
  return getAccessToken();
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, auth = true, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };

  if (auth) {
    const token = await ensureFreshToken();
    if (!token) {
      throw new ApiError("Your session expired. Sign in again.", { code: "UNAUTHENTICATED", status: 401 });
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let payload: BodyInit | undefined;
  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${env.apiBaseUrl}${path}`, { method, headers, body: payload, signal });
  } catch {
    throw new ApiError("Cannot reach the ResumeIQ API. Check your connection and try again.", {
      code: "NETWORK_ERROR",
    });
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  const data: unknown = text ? safeJson(text) : null;

  if (!response.ok) {
    const parsed = data as { error?: { code?: string; message?: string; details?: Record<string, unknown>; request_id?: string } } | null;
    throw new ApiError(parsed?.error?.message ?? `Request failed (${response.status})`, {
      code: parsed?.error?.code ?? "HTTP_ERROR",
      status: response.status,
      details: parsed?.error?.details,
      requestId: parsed?.error?.request_id,
    });
  }

  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) => request<T>(path, { method: "POST", formData }),
  public: <T>(path: string) => request<T>(path, { auth: false }),
};
