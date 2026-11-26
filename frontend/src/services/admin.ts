import { api } from "@/lib/api";
import type { AdminMetrics, AdminUser, Page } from "@/types";

export const adminApi = {
  metrics: () => api.get<AdminMetrics>("/v1/admin/metrics"),
  users: (search = "", limit = 25, offset = 0) =>
    api.get<Page<AdminUser>>(`/v1/admin/users?limit=${limit}&offset=${offset}${search ? `&search=${encodeURIComponent(search)}` : ""}`),
  updateUser: (id: string, patch: { role?: "user" | "administrator"; plan?: "free" | "pro" | "premium" }) =>
    api.patch<AdminUser>(`/v1/admin/users/${id}`, patch),
  scoring: () => api.get<Record<string, number>>("/v1/admin/settings/scoring"),
  updateScoring: (weights: Record<string, number>) => api.patch<Record<string, number>>("/v1/admin/settings/scoring", weights),
  health: () => api.get<Record<string, unknown>>("/v1/admin/health"),
};
