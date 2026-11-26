import { api } from "@/lib/api";
import type { Me } from "@/types";

export const accountApi = {
  me: () => api.get<Me>("/v1/me"),
  updateProfile: (patch: { full_name?: string; headline?: string; career_domain_id?: string | null; onboarding_completed?: boolean }) =>
    api.patch<Me>("/v1/me", patch),
  exportData: () => api.post<{ url: string; expires_in: string }>("/v1/me/export"),
  deleteAccount: () => api.delete<void>("/v1/me"),
};
