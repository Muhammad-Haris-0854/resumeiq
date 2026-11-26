import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, Terminal } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function MockCheckoutPage() {
  const [params] = useSearchParams();
  const plan = params.get("plan") ?? "pro";
  const interval = params.get("interval") ?? "month";
  const amount = Number(params.get("amount") ?? 0);
  const success = params.get("success") ?? "/billing/success";

  const command = `PAYMENT_WEBHOOK_SECRET=dev-webhook-secret python tools/mock_webhook.py \\
  --user <your-supabase-user-id> --plan ${plan} --interval ${interval} --amount ${amount}`;

  return (
    <div className="mx-auto max-w-2xl px-5 py-16">
      <p className="label">Mock checkout</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight">This environment uses the mock payment provider</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        No card is charged. A plan only activates when the API receives a webhook with a valid signature, so this page
        cannot fake a payment. Run the command below to complete the {plan} ({interval}) subscription.
      </p>

      <div className="mt-6 rounded-2xl bg-navy-900 p-4 text-slate-200">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Terminal className="h-3.5 w-3.5" /> terminal
        </div>
        <pre className="mt-2 overflow-x-auto text-xs leading-relaxed">{command}</pre>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={() => {
            void navigator.clipboard.writeText(command);
          }}
        >
          Copy command
        </Button>
        <Link to={success}>
          <Button>I have run it</Button>
        </Link>
      </div>

      <Alert tone="info" className="mt-6" title="Why this is safe">
        The mock provider signs its payloads with PAYMENT_WEBHOOK_SECRET, which never reaches the browser. Switch
        PAYMENT_PROVIDER=stripe and add real keys to use Stripe Checkout instead.
      </Alert>
    </div>
  );
}

export function BillingSuccessPage() {
  const { refreshMe, me } = useAuth();

  useEffect(() => {
    void refreshMe();
  }, [refreshMe]);

  return (
    <div className="mx-auto max-w-lg px-5 py-20 text-center">
      <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
      <h1 className="mt-4 text-2xl font-bold tracking-tight">Payment received</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        Your plan updates as soon as the payment provider confirms it server-side. If your plan still shows{" "}
        <span className="font-medium text-ink">{me?.entitlements.plan ?? "free"}</span>, wait a few seconds and refresh.
      </p>
      <Link to="/dashboard" className="mt-6 inline-block">
        <Button>Back to dashboard</Button>
      </Link>
    </div>
  );
}
