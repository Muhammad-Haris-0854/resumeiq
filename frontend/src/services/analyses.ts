import { api } from "@/lib/api";
import type { Analysis, Issue, IssueStatus, Page } from "@/types";

export const analysesApi = {
  list: (limit = 20, offset = 0) => api.get<Page<Analysis>>(`/v1/analyses?limit=${limit}&offset=${offset}`),
  get: (id: string) => api.get<Analysis>(`/v1/analyses/${id}`),
  create: (payload: { resume_version_id: string; career_domain_id: string; job_description_id?: string }) =>
    api.post<Analysis>("/v1/analyses", payload),
  rerun: (id: string) => api.post<Analysis>(`/v1/analyses/${id}/rerun`),
  remove: (id: string) => api.delete<void>(`/v1/analyses/${id}`),
  compare: (id: string, otherId: string) =>
    api.get<{ base_id: string; compare_id: string; overall_delta: number; deltas: Record<string, number> }>(
      `/v1/analyses/${id}/compare/${otherId}`,
    ),
  updateIssue: (analysisId: string, issueId: string, status: IssueStatus, userEdit?: string) =>
    api.patch<Issue>(`/v1/analyses/${analysisId}/issues/${issueId}`, { status, user_edit: userEdit }),
};
