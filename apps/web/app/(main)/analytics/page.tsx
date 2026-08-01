// Empty state — Closet Analytics lands starting Phase 2 (Sprint 7), full set in
// Phase 5. See docs/design/ui-wireframes.md screen 9.
export default function AnalyticsPage() {
  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Analytics</p>
        <h1 className="font-display text-2xl">Nothing to show yet</h1>
      </div>
      <div className="rounded-lg border border-dashed border-line p-8 text-center">
        <p className="text-sm text-ink-soft">
          Wear stats, cost-per-wear, and rediscovery suggestions show up here once you&apos;ve
          logged a few outfits.
        </p>
      </div>
    </main>
  );
}
