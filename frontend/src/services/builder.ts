import { api } from "@/lib/api";
import type { GeneratedResume, Page, ResumeContent, Template } from "@/types";

export const builderApi = {
  list: (limit = 20, offset = 0) => api.get<Page<GeneratedResume>>(`/v1/generated-resumes?limit=${limit}&offset=${offset}`),
  get: (id: string) => api.get<GeneratedResume>(`/v1/generated-resumes/${id}`),
  create: (payload: { template_id: string; title: string; resume_version_id?: string; content?: ResumeContent }) =>
    api.post<GeneratedResume>("/v1/generated-resumes", payload),
  save: (id: string, content: ResumeContent) => api.put<GeneratedResume>(`/v1/generated-resumes/${id}`, content),
  export: (id: string) => api.post<GeneratedResume>(`/v1/generated-resumes/${id}/export`),
  versions: (id: string) => api.get<{ items: Array<{ version: number; created_at?: string }> }>(`/v1/generated-resumes/${id}/versions`),
  restore: (id: string, version: number) => api.post<GeneratedResume>(`/v1/generated-resumes/${id}/versions/${version}/restore`),
  templates: () => api.get<Template[]>("/v1/templates"),
};
