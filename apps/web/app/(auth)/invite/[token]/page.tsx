"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type ValidateResponse = { valid: boolean; email?: string; reason?: string };

const REASON_COPY: Record<string, string> = {
  not_found: "This invite link doesn't exist.",
  already_used: "This invite has already been used.",
  expired: "This invite link has expired — ask for a new one.",
};

export default function InvitePage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();

  const [status, setStatus] = useState<"checking" | "valid" | "invalid">("checking");
  const [email, setEmail] = useState<string>("");
  const [reason, setReason] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Public endpoint — no auth header needed to validate a token.
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/invites/${token}`)
      .then((res) => res.json())
      .then((data: ValidateResponse) => {
        if (data.valid && data.email) {
          setEmail(data.email);
          setStatus("valid");
        } else {
          setReason(data.reason ?? "not_found");
          setStatus("invalid");
        }
      })
      .catch(() => {
        setReason("not_found");
        setStatus("invalid");
      });
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const supabase = createClient();
    const { error: signUpError } = await supabase.auth.signUp({ email, password });
    if (signUpError) {
      setError(signUpError.message);
      setSubmitting(false);
      return;
    }

    try {
      await apiFetch("/auth/invites/accept", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
    } catch (err) {
      setError(err instanceof ApiError ? "Couldn't link this invite to your account." : "Something went wrong.");
      setSubmitting(false);
      return;
    }

    router.push("/onboarding/consent");
  }

  if (status === "checking") {
    return <main className="p-6 text-sm text-ink-soft">Checking invite...</main>;
  }

  if (status === "invalid") {
    return (
      <main className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center gap-2 px-6 text-center">
        <h1 className="font-display text-xl">Invite not valid</h1>
        <p className="text-sm text-ink-soft">{REASON_COPY[reason ?? "not_found"]}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">You&apos;re invited</p>
        <h1 className="font-display text-2xl">Set up your Muse account</h1>
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-lg border border-line bg-bg-elevated p-4 shadow-sm"
      >
        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs text-ink-soft">Email</span>
          <p className="rounded-md border border-line bg-bg px-3 py-2 text-sm text-ink-soft">
            {email}
          </p>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="font-mono text-xs text-ink-soft">
            Choose a password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-line bg-bg px-3 py-2 text-sm"
          />
        </div>
        {error && <p className="text-xs text-accent">{error}</p>}
        <Button type="submit" disabled={submitting}>
          {submitting ? "Creating account..." : "Continue"}
        </Button>
      </form>

      <p className="text-center text-xs text-ink-faint">
        Next: a quick screen about the Terms &amp; how your photos are used — takes a minute to
        read, and it&apos;s worth it.
      </p>
    </main>
  );
}
