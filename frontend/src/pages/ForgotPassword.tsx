import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/field";
import { ApiError } from "@/lib/api";
import { requestPasswordReset } from "@/services/auth";

const schema = z.object({ email: z.string().email("Enter a valid email address") });
type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "" } });

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      await requestPasswordReset(values.email);
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send the reset email.");
    }
  });

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Reset your password</h1>
      <p className="mt-1.5 text-sm text-slate-600">We will email you a link to choose a new password.</p>

      {error && <Alert tone="danger" className="mt-5">{error}</Alert>}
      {sent && (
        <Alert tone="success" className="mt-5" title="Check your inbox">
          If an account exists for that address, a reset link is on its way.
        </Alert>
      )}

      <form className="mt-6 space-y-4" onSubmit={onSubmit} noValidate>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />
        </div>
        <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
          Send reset link
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700">Back to sign in</Link>
      </p>
    </div>
  );
}
