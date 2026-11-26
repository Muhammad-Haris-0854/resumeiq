import { Route, Routes } from "react-router-dom";

import { AppShell } from "@/app/AppShell";
import { AuthLayout } from "@/app/AuthLayout";
import { MarketingLayout } from "@/app/MarketingLayout";
import { RequireAdmin, RequireAuth } from "@/app/guards";
import { AdminPage } from "@/pages/Admin";
import { AnalysisPage } from "@/pages/Analysis";
import { BuilderPage } from "@/pages/Builder";
import { CareerPage } from "@/pages/Career";
import { DashboardPage } from "@/pages/Dashboard";
import { EditorPage } from "@/pages/Editor";
import { FeaturesPage } from "@/pages/Features";
import { ForgotPasswordPage } from "@/pages/ForgotPassword";
import { JobMatchPage } from "@/pages/JobMatch";
import { LandingPage } from "@/pages/Landing";
import { LoginPage } from "@/pages/Login";
import { MockCheckoutPage, BillingSuccessPage } from "@/pages/Billing";
import { NotFoundPage } from "@/pages/NotFound";
import { PricingPage } from "@/pages/Pricing";
import { SettingsPage } from "@/pages/Settings";
import { SignupPage } from "@/pages/Signup";
import { SubscriptionPage } from "@/pages/Subscription";
import { TemplatesPage } from "@/pages/Templates";
import { UploadPage } from "@/pages/Upload";
import { ResetPasswordPage } from "@/pages/ResetPassword";

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell>{children}</AppShell>
    </RequireAuth>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/pricing" element={<PricingPage />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>

      <Route path="/billing/mock-checkout" element={<MockCheckoutPage />} />
      <Route
        path="/billing/success"
        element={
          <RequireAuth>
            <BillingSuccessPage />
          </RequireAuth>
        }
      />

      <Route path="/dashboard" element={<Shell><DashboardPage /></Shell>} />
      <Route path="/resumes/upload" element={<Shell><UploadPage /></Shell>} />
      <Route path="/career" element={<Shell><CareerPage /></Shell>} />
      <Route path="/analyses/:analysisId" element={<Shell><AnalysisPage /></Shell>} />
      <Route path="/job-match" element={<Shell><JobMatchPage /></Shell>} />
      <Route path="/builder" element={<Shell><BuilderPage /></Shell>} />
      <Route path="/builder/:generatedId" element={<Shell><EditorPage /></Shell>} />
      <Route path="/templates" element={<Shell><TemplatesPage /></Shell>} />
      <Route path="/subscription" element={<Shell><SubscriptionPage /></Shell>} />
      <Route path="/settings" element={<Shell><SettingsPage /></Shell>} />
      <Route
        path="/admin"
        element={
          <RequireAdmin>
            <AppShell>
              <AdminPage />
            </AppShell>
          </RequireAdmin>
        }
      />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
