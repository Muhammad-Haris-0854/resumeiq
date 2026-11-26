import { api } from "@/lib/api";
import type { Invoice, Plan, Subscription } from "@/types";

export const billingApi = {
  plans: () => api.public<Plan[]>("/v1/billing/plans"),
  subscription: () => api.get<Subscription>("/v1/billing/subscription"),
  checkout: (plan_code: "pro" | "premium", interval: "month" | "year") =>
    api.post<{ checkout_url: string; session_id: string }>("/v1/billing/checkout", { plan_code, interval }),
  portal: () => api.post<{ portal_url: string }>("/v1/billing/portal"),
  cancel: () => api.post<Subscription>("/v1/billing/cancel"),
  invoices: () => api.get<Invoice[]>("/v1/billing/invoices"),
};
