import { Button } from "@/components/ui/Button";

// Empty state — Phase 1 (Sprint 3-5) wires this to real generated outfits.
// See docs/design/ui-wireframes.md screen 1.
export default function TodayPage() {
  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Today</p>
        <h1 className="font-display text-2xl">Nothing styled yet</h1>
      </div>
      <div className="rounded-lg border border-dashed border-line p-8 text-center">
        <p className="text-sm text-ink-soft">
          Add a few items to your wardrobe and Muse will start suggesting outfits here.
        </p>
      </div>
      <Button className="self-start">Add item</Button>
    </main>
  );
}
