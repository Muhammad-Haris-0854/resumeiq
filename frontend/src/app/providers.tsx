import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "@/hooks/useAuth";
import { ToastProvider } from "@/hooks/useToast";
import { ApiError } from "@/lib/api";
import { ConfigBanner } from "@/components/ConfigBanner";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
              if (error instanceof ApiError && error.code === "API_NOT_CONFIGURED") return false;
              if (error instanceof ApiError && [401, 403, 404, 429, 422].includes(error.status)) return false;
              return failureCount < 2;
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter basename={import.meta.env.BASE_URL}>
          <AuthProvider>{children}</AuthProvider>
          <ConfigBanner />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
