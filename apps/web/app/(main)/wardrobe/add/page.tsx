"use client";

import { useRouter } from "next/navigation";
import { ALL_CATEGORIES, isSensitiveCategory } from "@/lib/categories";
import { Chip } from "@/components/ui/Chip";

// Category picker is the FIRST step, not the camera — this is what lets a
// sensitive category route to the manual-entry screen instead of the AI photo
// pipeline. See docs/design/ui-wireframes.md screen 3 / 3a.
export default function AddItemCategoryPage() {
  const router = useRouter();

  function handlePick(category: string) {
    if (isSensitiveCategory(category)) {
      router.push(`/wardrobe/add/manual?category=${category}`);
    } else {
      router.push(`/wardrobe/add/camera?category=${category}`);
    }
  }

  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Add item</p>
        <h1 className="font-display text-2xl">What are you adding?</h1>
      </div>
      <div className="flex flex-wrap gap-2">
        {ALL_CATEGORIES.map((category) => (
          <Chip key={category} onClick={() => handlePick(category)} className="capitalize">
            {category}
          </Chip>
        ))}
      </div>
      <p className="text-xs text-ink-faint">
        Underwear/lingerie skip the camera — you&apos;ll get a quick text form instead, and the
        photo never leaves your account if you add one anyway.
      </p>
    </main>
  );
}
