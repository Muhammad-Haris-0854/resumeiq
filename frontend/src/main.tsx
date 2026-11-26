import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Providers } from "@/app/providers";
import { consumeSpaRedirect } from "@/lib/spa-redirect";
import { AppRoutes } from "@/app/router";
import "@/index.css";

// Restore a deep link captured by public/404.html before the router mounts.
consumeSpaRedirect();

const container = document.getElementById("root");
if (!container) throw new Error("Root element missing from index.html");

createRoot(container).render(
  <StrictMode>
    <Providers>
      <AppRoutes />
    </Providers>
  </StrictMode>,
);
