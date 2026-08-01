import { Button } from "@/components/ui/Button";

// Empty state — ingestion pipeline (§5.1) and the real grid land in Phase 1.
// See docs/design/ui-wireframes.md screen 2.
export default function WardrobePage() {
  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Wardrobe</p>
        <h1 className="font-display text-2xl">Your closet is empty</h1>
      </div>
      <div className="rounded-lg border border-dashed border-line p-8 text-center">
        <p className="text-sm text-ink-soft">
          Photograph an item and Muse will background-remove and tag it automatically.
        </p>
      </div>
      <Button className="self-start">+ Add item</Button>
    </main>
  );
}
