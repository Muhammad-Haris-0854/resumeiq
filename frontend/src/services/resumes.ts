import { api } from "@/lib/api";
import type { Page, Resume, ResumeDetail, ResumeVersion } from "@/types";

export const resumesApi = {
  list: (limit = 20, offset = 0) => api.get<Page<Resume>>(`/v1/resumes?limit=${limit}&offset=${offset}`),
  get: (id: string) => api.get<ResumeDetail>(`/v1/resumes/${id}`),
  upload: (file: File, title: string, careerDomainId?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    if (careerDomainId) form.append("career_domain_id", careerDomainId);
    return api.upload<Resume>("/v1/resumes", form);
  },
  addVersion: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.upload<ResumeVersion>(`/v1/resumes/${id}/versions`, form);
  },
  update: (id: string, patch: { title?: string; career_domain_id?: string | null }) =>
    api.patch<Resume>(`/v1/resumes/${id}`, patch),
  remove: (id: string) => api.delete<void>(`/v1/resumes/${id}`),
  downloadUrl: (id: string) => api.get<{ url: string; expires_in: number }>(`/v1/resumes/${id}/download`),
  preview: (id: string) =>
    api.get<{ status: string; method: string | null; page_count: number | null; text: string; truncated: boolean }>(
      `/v1/resumes/${id}/preview`,
    ),
  reprocess: (id: string) => api.post<{ status: string }>(`/v1/resumes/${id}/reprocess`),
};
