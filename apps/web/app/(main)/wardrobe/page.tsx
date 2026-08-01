"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { STANDARD_CATEGORIES } from "@/lib/categories";

type GarmentListItem = {
  id: string;
  category: string;
  primary_color: string | null;
  status: string;
  entry_mode: string;
  images: { storage_url: string; is_primary: boolean }[];
};

export default function WardrobePage() {
  const [garments, setGarments] = useState<GarmentListItem[] | null>(null);
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    const query = category ? `?category=${category}` : "";
    apiFetch<GarmentListItem[]>(`/garments${query}`)
      .then(setGarments)
      .catch(() => setGarments([]));
  }, [category]);

  return (
    <main className="flex flex-col gap-4 px-6 pt-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Wardrobe</p>
          <h1 className="font-display text-2xl">
            {garments?.length ? `${garments.length} items` : "Your closet"}
          </h1>
        </div>
        <Link href="/wardrobe/add">
          <Button>+ Add</Button>
        </Link>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        <Chip active={category === null} onClick={() => setCategory(null)}>
          All
        </Chip>
        {STANDARD_CATEGORIES.map((c) => (
          <Chip key={c} active={category === c} onClick={() => setCategory(c)} className="capitalize">
            {c}
          </Chip>
        ))}
      </div>

      {garments === null && <p className="text-sm text-ink-soft">Loading...</p>}

      {garments?.length === 0 && (
        <div className="rounded-lg border border-dashed border-line p-8 text-center">
          <p className="text-sm text-ink-soft">
            {category
              ? `No ${category} items yet.`
              : "Photograph an item and Muse will background-remove and tag it automatically."}
          </p>
        </div>
      )}

      {garments && garments.length > 0 && (
        <div className="grid grid-cols-2 gap-3 pb-4">
          {garments.map((g) => {
            const primaryImage = g.images.find((img) => img.is_primary) ?? g.images[0];
            return (
              <Link
                key={g.id}
                href={`/wardrobe/${g.id}`}
                className="flex flex-col gap-1 rounded-lg border border-line bg-bg-elevated p-2"
              >
                <div className="aspect-square rounded-md bg-secondary-soft">
                  {primaryImage && (
                    // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
                    <img
                      src={primaryImage.storage_url}
                      alt=""
                      className="h-full w-full rounded-md object-contain"
                    />
                  )}
                </div>
                <p className="text-xs capitalize text-ink-soft">
                  {g.category}
                  {g.status === "processing" && " · processing"}
                </p>
              </Link>
            );
          })}
        </div>
      )}
    </main>
  );
}
