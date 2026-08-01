"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";

type GarmentImage = { id: string; storage_url: string; is_primary: boolean };
type GarmentDetail = {
  id: string;
  category: string;
  subcategory: string | null;
  primary_color: string | null;
  pattern: string | null;
  season: string[] | null;
  occasion: string[] | null;
  formality_score: number | null;
  ai_description: string | null;
  status: string;
  entry_mode: string;
  manual_description: string | null;
  manual_quantity: number | null;
  is_favorite: boolean;
  images: GarmentImage[];
};

export default function GarmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [garment, setGarment] = useState<GarmentDetail | null>(null);

  useEffect(() => {
    apiFetch<GarmentDetail>(`/garments/${id}`)
      .then(setGarment)
      .catch(() => router.push("/wardrobe"));
  }, [id, router]);

  async function toggleFavorite() {
    if (!garment) return;
    const updated = await apiFetch<GarmentDetail>(`/garments/${garment.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_favorite: !garment.is_favorite }),
    });
    setGarment({ ...garment, is_favorite: updated.is_favorite });
  }

  if (!garment) {
    return <main className="p-6 text-sm text-ink-soft">Loading...</main>;
  }

  if (garment.entry_mode === "manual") {
    return (
      <main className="flex flex-col gap-4 px-6 pt-8">
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint capitalize">
          {garment.category}
        </p>
        <h1 className="font-display text-2xl">{garment.manual_description}</h1>
        {garment.manual_quantity && (
          <p className="text-sm text-ink-soft">Quantity: {garment.manual_quantity}</p>
        )}
        <p className="text-xs text-ink-faint">
          Manually entered — no photo processed, excluded from outfit suggestions.
        </p>
      </main>
    );
  }

  return (
    <main className="flex flex-col gap-4 px-6 pt-8">
      {garment.images[0] && (
        // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
        <img
          src={garment.images[0].storage_url}
          alt=""
          className="h-72 w-full rounded-lg bg-secondary-soft object-contain"
        />
      )}

      <div className="flex items-center justify-between">
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint capitalize">
          {garment.category}
          {garment.subcategory ? ` · ${garment.subcategory}` : ""}
        </p>
        <Button variant="secondary" onClick={toggleFavorite}>
          {garment.is_favorite ? "★ Favorited" : "☆ Favorite"}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {garment.primary_color && <Chip active>{garment.primary_color}</Chip>}
        {garment.pattern && <Chip>{garment.pattern}</Chip>}
        {garment.occasion?.map((o) => <Chip key={o}>{o}</Chip>)}
        {garment.season?.map((s) => <Chip key={s}>{s}</Chip>)}
      </div>

      {garment.ai_description && <p className="text-sm text-ink-soft">{garment.ai_description}</p>}

      {garment.status === "processing" && (
        <p className="text-xs text-ink-faint">Still processing — attributes will fill in shortly.</p>
      )}
    </main>
  );
}
