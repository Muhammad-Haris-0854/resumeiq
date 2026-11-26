import { api } from "@/lib/api";
import type { Domain, DomainDetail, Template } from "@/types";

export const catalogApi = {
  domains: () => api.get<Domain[]>("/v1/domains"),
  domain: (slug: string) => api.get<DomainDetail>(`/v1/domains/${slug}`),
  templates: () => api.get<Template[]>("/v1/templates"),
};
