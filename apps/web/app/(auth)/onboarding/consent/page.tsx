"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Toggle } from "@/components/ui/Toggle";

// Bump this whenever the T&C copy below materially changes — it's stored per-user
// as tc_version (docs/PRD.md §7.1) so a future rewrite can tell who's on stale
// consent. The placeholder text below is NOT the final copy — the developer is
// writing that personally in their own voice; this file just guarantees the
// structural requirements (toggle co-located, scroll-to-enable, required
// disclosures) are met regardless of what the final words say.
const TC_VERSION = "placeholder-v0";

export default function ConsentPage() {
  const router = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrolledToEnd, setScrolledToEnd] = useState(false);
  const [devPhotoAccess, setDevPhotoAccess] = useState(true); // default ON — see PRD §7.1 item 2
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const reachedEnd = el.scrollTop + el.clientHeight >= el.scrollHeight - 24;
    if (reachedEnd) setScrolledToEnd(true);
  }

  async function handleAgree() {
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch("/users/me/consent", {
        method: "PUT",
        body: JSON.stringify({
          consent_dev_photo_access: devPhotoAccess,
          tc_version: TC_VERSION,
        }),
      });
      router.push("/onboarding/profile");
    } catch {
      setError("Couldn't save that — check your connection and try again.");
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col gap-4 px-6 py-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
          Before you get started
        </p>
        <h1 className="font-display text-2xl">Terms &amp; how this works</h1>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex max-h-72 flex-col gap-3 overflow-y-auto rounded-lg border border-line bg-bg-elevated p-4 text-sm text-ink-soft"
      >
        <p className="italic text-ink-faint">
          [Placeholder — final T&amp;C copy goes here, written by the developer in their own
          voice. The two disclosures below must survive into that copy: dev photo access, and
          the sensitive-content/Gemini note.]
        </p>
        <p>
          This app is a personal project — not a public product. Your wardrobe, outfits, and
          chat history are private to your account, isolated at the database level from every
          other account, including the developer&apos;s own.
        </p>
        <p>
          Uploaded photos are sent to Google&apos;s Gemini API for clothing analysis. On Gemini&apos;s
          free tier, Google may use submitted photos to improve its models, and human reviewers
          may read/annotate them. Please don&apos;t upload underwear, lingerie, or similar photos —
          use manual entry instead (no photo required) for those items.
        </p>
        <p>
          The developer may occasionally want a copy of an uploaded photo for debugging. That&apos;s
          the toggle below — on by default, and you can turn it off any time in Settings.
        </p>
        <p className="pt-2 text-xs text-ink-faint">— end of terms —</p>
      </div>

      <div className="flex items-center justify-between gap-3 rounded-lg border border-line bg-bg-elevated p-4">
        <div>
          <p className="text-sm font-medium">Developer photo access</p>
          <p className="text-xs text-ink-soft">
            Lets the developer see a copy of your photos for debugging. Revocable any time.
          </p>
        </div>
        <Toggle
          checked={devPhotoAccess}
          onChange={setDevPhotoAccess}
          label="Developer photo access"
        />
      </div>

      {error && <p className="text-xs text-accent">{error}</p>}

      <Button onClick={handleAgree} disabled={!scrolledToEnd || submitting}>
        {scrolledToEnd ? (submitting ? "Saving..." : "I agree") : "Scroll to read — then agree"}
      </Button>
    </main>
  );
}
