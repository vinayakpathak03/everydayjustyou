// Empty state — tool-calling chat lands in Phase 3 (Sprint 8-9).
// See docs/design/ui-wireframes.md screen 8, system-architecture.md §5.3.
export default function StylistPage() {
  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Stylist</p>
        <h1 className="font-display text-2xl">Not chatting yet</h1>
      </div>
      <div className="rounded-lg border border-dashed border-line p-8 text-center">
        <p className="text-sm text-ink-soft">
          Once you&apos;ve added some items, ask things like &ldquo;what should I wear for
          dinner?&rdquo;
        </p>
      </div>
    </main>
  );
}
