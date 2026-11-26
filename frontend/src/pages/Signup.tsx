import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldError, Hint, Input, Label } from "@/components/ui/field";
import { ApiError } from "@/lib/api";
import { signInWithGoogle, signUp } from "@/services/auth";

const schema = z
  .object({
    fullName: z.string().min(2, "Enter your full name").max(120),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .min(8, "Use at least 8 characters")
      .regex(/[A-Za-z]/, "Include at least one letter")
      .regex(/\d/, "Include at least one number"),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  });

type FormValues = z.infer<typeof schema>;

export function SignupPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [needsVerification, setNeedsVerification] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { fullName: "", email: "", password: "", confirm: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const result = await signUp(values.email, values.password, values.fullName);
      if (result.needsVerification) {
        setNeedsVerification(true);
      } else {
        navigate("/career", { replace: true });
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign up failed. Try again.");
    }
  });

  if (needsVerification) {
    return (
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Check your email</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          We sent a verification link to <span className="font-medium text-ink">{form.getValues("email")}</span>. Open it
          to activate your account, then sign in.
        </p>
        <Link to="/login" className="mt-6 inline-block">
          <Button variant="outline">Back to sign in</Button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
      <p className="mt-1.5 text-sm text-slate-600">Two free analyses a month. No card required.</p>

      {error && <Alert tone="danger" className="mt-5">{error}</Alert>}

      <form className="mt-6 space-y-4" onSubmit={onSubmit} noValidate>
        <div>
          <Label htmlFor="fullName">Full name</Label>
          <Input id="fullName" autoComplete="name" placeholder="Muhammad Haris" {...form.register("fullName")} />
          <FieldError message={form.formState.errors.fullName?.message} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" autoComplete="new-password" {...form.register("password")} />
          <Hint>At least 8 characters, with a letter and a number.</Hint>
          <FieldError message={form.formState.errors.password?.message} />
        </div>
        <div>
          <Label htmlFor="confirm">Confirm password</Label>
          <Input id="confirm" type="password" autoComplete="new-password" {...form.register("confirm")} />
          <FieldError message={form.formState.errors.confirm?.message} />
        </div>
        <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
          Create account
        </Button>
      </form>

      <Button
        variant="outline"
        className="mt-3 w-full"
        onClick={() => void signInWithGoogle().catch(() => setError("Google sign-in could not start."))}
      >
        Continue with Google
      </Button>

      <p className="mt-6 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700">
          Sign in
        </Link>
      </p>
      <p className="mt-4 text-center text-xs leading-relaxed text-slate-500">
        By creating an account you agree that uploaded resumes are processed to generate your analysis and are never
        used to train AI models.
      </p>
    </div>
  );
}
