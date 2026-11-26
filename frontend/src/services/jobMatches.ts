import { api } from "@/lib/api";
import type { JobMatch, Page } from "@/types";

export const jobMatchesApi = {
  list: (limit = 20, offset = 0) => api.get<Page<JobMatch>>(`/v1/job-matches?limit=${limit}&offset=${offset}`),
  get: (id: string) => api.get<JobMatch>(`/v1/job-matches/${id}`),
  create: (payload: { resume_version_id: string; title?: string; company?: string; raw_text: string }) =>
    api.post<JobMatch>("/v1/job-matches", payload),
};
