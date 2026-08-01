"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";

// Real style-profile capture (sizes, preferred aesthetics, location) is Sprint 9
// work per docs/roadmap/roadmap-and-sprints.md — the `style_profiles` table exists
// from Phase 0 (see services/api/app/models/style_profile.py) but no endpoint reads
// or writes it yet. This screen is a placeholder step so onboarding has somewhere
// to go after consent instead of dead-ending, not the real feature.
export default function OnboardingProfilePage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6 text-center">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Almost there</p>
        <h1 className="font-display text-2xl">Your style profile</h1>
        <p className="mt-2 text-sm text-ink-soft">
          Sizes, colors, and aesthetic preferences help the AI Stylist — coming soon. For now,
          let&apos;s get your wardrobe started.
        </p>
      </div>
      <Button onClick={() => router.push("/today")}>Continue to Muse</Button>
    </main>
  );
}
