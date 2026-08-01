"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type OutfitItem = {
  garment_id: string;
  slot: string;
  category: string;
  primary_color: string | null;
  image_url: string | null;
};
type OutfitOut = {
  id: string;
  score: number;
  rationale: string | null;
  items: OutfitItem[];
};

function currentSeason(): string {
  const month = new Date().getMonth() + 1; // 1-12
  if ([12, 1, 2].includes(month)) return "winter";
  if ([3, 4, 5].includes(month)) return "spring";
  if ([6, 7, 8].includes(month)) return "summer";
  return "fall";
}

function OutfitThumb({ outfit }: { outfit: OutfitOut }) {
  const cover = outfit.items.find((i) => i.image_url)?.image_url;
  return (
    <Link
      href={`/outfits/${outfit.id}`}
      className="flex flex-col gap-1 rounded-lg border border-line bg-bg-elevated p-2"
    >
      <div className="flex h-40 items-center justify-center rounded-md bg-secondary-soft">
        {cover ? (
          // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
          <img src={cover} alt="" className="h-full w-full rounded-md object-contain" />
        ) : (
          <span className="text-xs text-ink-faint">{outfit.items.length} pieces</span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-ink-faint">
          {outfit.items.map((i) => i.category).join(" · ")}
        </span>
        <span className="rounded-full bg-accent px-2 py-0.5 font-mono text-[10px] text-accent-ink">
          {outfit.score}
        </span>
      </div>
    </Link>
  );
}

export default function TodayPage() {
  const [outfits, setOutfits] = useState<OutfitOut[] | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "empty" | "error">("loading");

  useEffect(() => {
    apiFetch<OutfitOut[]>("/outfits/generate", {
      method: "POST",
      body: JSON.stringify({ season: currentSeason(), count: 3 }),
    })
      .then((result) => {
        setOutfits(result);
        setState("ready");
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 422) {
          setState("empty");
        } else {
          setState("error");
        }
      });
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 pt-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Today</p>
        <h1 className="font-display text-2xl">
          {state === "ready" ? "Today's looks" : "Nothing styled yet"}
        </h1>
      </div>

      {state === "loading" && (
        <div className="h-56 animate-pulse rounded-lg bg-secondary-soft" />
      )}

      {state === "empty" && (
        <div className="rounded-lg border border-dashed border-line p-8 text-center">
          <p className="text-sm text-ink-soft">
            Add a top or dress, a bottom (if no dress), and shoes — Muse needs at least that much
            to build an outfit.
          </p>
        </div>
      )}

      {state === "error" && (
        <div className="rounded-lg border border-dashed border-line p-8 text-center">
          <p className="text-sm text-ink-soft">Couldn&apos;t generate outfits — try again shortly.</p>
        </div>
      )}

      {state === "ready" && outfits && outfits.length > 0 && (
        <>
          <Link href={`/outfits/${outfits[0].id}`} className="flex flex-col gap-2">
            <div className="flex h-72 items-center justify-center rounded-lg bg-secondary-soft">
              {outfits[0].items.find((i) => i.image_url) ? (
                // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
                <img
                  src={outfits[0].items.find((i) => i.image_url)!.image_url!}
                  alt=""
                  className="h-full w-full rounded-lg object-contain"
                />
              ) : (
                <span className="text-sm text-ink-faint">
                  {outfits[0].items.map((i) => i.category).join(" · ")}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-accent px-3 py-1 font-mono text-xs text-accent-ink">
                {outfits[0].score}
              </span>
              {outfits[0].rationale && (
                <p className="line-clamp-2 text-sm text-ink-soft">{outfits[0].rationale}</p>
              )}
            </div>
          </Link>

          {outfits.length > 1 && (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {outfits.slice(1).map((o) => (
                <div key={o.id} className="w-40 flex-none">
                  <OutfitThumb outfit={o} />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <Link href="/wardrobe/add">
        <Button variant="secondary" className="self-start">
          Add item
        </Button>
      </Link>
    </main>
  );
}
