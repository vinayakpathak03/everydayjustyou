"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type OutfitItem = {
  garment_id: string;
  slot: string;
  category: string;
  primary_color: string | null;
  image_url: string | null;
};
type OutfitDetail = {
  id: string;
  score: number;
  score_breakdown: Record<string, number> | null;
  rationale: string | null;
  items: OutfitItem[];
};

export default function OutfitDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [outfit, setOutfit] = useState<OutfitDetail | null>(null);
  const [logging, setLogging] = useState(false);
  const [worn, setWorn] = useState(false);

  useEffect(() => {
    apiFetch<OutfitDetail>(`/outfits/${id}`).then(setOutfit);
  }, [id]);

  async function handleWearToday() {
    setLogging(true);
    try {
      await apiFetch("/wear-logs", {
        method: "POST",
        body: JSON.stringify({ outfit_id: id }),
      });
      setWorn(true);
    } finally {
      setLogging(false);
    }
  }

  if (!outfit) {
    return <main className="p-6 text-sm text-ink-soft">Loading...</main>;
  }

  return (
    <main className="flex flex-col gap-4 px-6 pt-8 pb-8">
      <button onClick={() => router.back()} className="self-start text-xs text-ink-faint">
        ← Back
      </button>

      <div className="flex items-center gap-2">
        <span className="rounded-full bg-accent px-3 py-1 font-mono text-sm text-accent-ink">
          {outfit.score}
        </span>
        <h1 className="font-display text-xl">Why this works</h1>
      </div>
      {outfit.rationale && <p className="text-sm text-ink-soft">{outfit.rationale}</p>}

      <div className="grid grid-cols-2 gap-3">
        {outfit.items.map((item) => (
          <div key={item.garment_id} className="flex flex-col gap-1 rounded-lg border border-line p-2">
            <div className="flex h-32 items-center justify-center rounded-md bg-secondary-soft">
              {item.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
                <img src={item.image_url} alt="" className="h-full w-full rounded-md object-contain" />
              ) : (
                <span className="text-xs text-ink-faint">{item.category}</span>
              )}
            </div>
            <p className="font-mono text-[10px] uppercase text-ink-faint">{item.slot}</p>
          </div>
        ))}
      </div>

      {outfit.score_breakdown && (
        <div className="flex flex-wrap gap-2 text-xs text-ink-faint">
          {Object.entries(outfit.score_breakdown).map(([key, value]) => (
            <span key={key} className="rounded-full border border-line px-2 py-1">
              {key.replace(/_/g, " ")}: {Math.round(value)}
            </span>
          ))}
        </div>
      )}

      <Button onClick={handleWearToday} disabled={logging || worn}>
        {worn ? "Logged ✓" : logging ? "Logging..." : "Wear this today"}
      </Button>
    </main>
  );
}
