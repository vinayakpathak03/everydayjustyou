"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Toggle } from "@/components/ui/Toggle";

type ConsentOut = {
  consent_dev_photo_access: boolean;
  tc_version: string | null;
  tc_accepted_at: string | null;
};

// Real, not a stub — the dev-photo-access toggle here is the same field set on
// the onboarding consent screen (PRD §7.1: "revocable at any time"), so this
// needs to actually read/write it from day one, unlike the other empty-state pages.
export default function SettingsPage() {
  const router = useRouter();
  const [consent, setConsent] = useState<ConsentOut | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiFetch<ConsentOut>("/users/me/consent").then(setConsent).catch(() => setConsent(null));
  }, []);

  async function toggleConsent(next: boolean) {
    if (!consent) return;
    setSaving(true);
    setConsent({ ...consent, consent_dev_photo_access: next });
    try {
      const updated = await apiFetch<ConsentOut>("/users/me/consent", {
        method: "PUT",
        body: JSON.stringify({
          consent_dev_photo_access: next,
          tc_version: consent.tc_version ?? "placeholder-v0",
        }),
      });
      setConsent(updated);
    } finally {
      setSaving(false);
    }
  }

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/sign-in");
    router.refresh();
  }

  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Settings</p>
        <h1 className="font-display text-2xl">Profile</h1>
      </div>

      <div className="rounded-lg border border-line bg-bg-elevated p-4">
        <p className="mb-3 text-xs font-mono uppercase tracking-wide text-ink-faint">
          Privacy &amp; data
        </p>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium">Developer photo access</p>
            <p className="text-xs text-ink-soft">
              Lets the developer see a copy of your uploaded photos for debugging.
            </p>
          </div>
          {consent && (
            <Toggle
              checked={consent.consent_dev_photo_access}
              onChange={toggleConsent}
              disabled={saving}
              label="Developer photo access"
            />
          )}
        </div>
      </div>

      <Button variant="secondary" onClick={handleSignOut} className="self-start">
        Sign out
      </Button>
    </main>
  );
}
