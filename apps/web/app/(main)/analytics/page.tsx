"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type WearStat = {
  garment_id: string;
  category: string;
  primary_color: string | null;
  times_worn: number;
  last_worn_on: string | null;
  cost_per_wear: number | null;
};
type AnalyticsSummary = {
  most_worn: WearStat[];
  least_worn: WearStat[];
  cost_per_wear: WearStat[];
};

function StatRow({ label, entries, valueLabel }: {
  label: string;
  entries: WearStat[];
  valueLabel: (e: WearStat) => string;
}) {
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">{label}</p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {entries.map((e) => (
          <div
            key={e.garment_id}
            className="flex w-28 flex-none flex-col gap-1 rounded-lg border border-line bg-bg-elevated p-2"
          >
            <div className="h-16 rounded-md bg-secondary-soft" />
            <p className="truncate text-xs capitalize text-ink-soft">
              {e.primary_color ? `${e.primary_color} ` : ""}
              {e.category}
            </p>
            <p className="font-mono text-[10px] text-ink-faint">{valueLabel(e)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Wired to GET /analytics/summary (Phase 2) — most/least worn and cost-per-wear.
// Capsule suggestions, duplicates, and seasonal rotation are Phase 5.
export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    apiFetch<AnalyticsSummary>("/analytics/summary")
      .then((d) => {
        setData(d);
        setEmpty(d.most_worn.length === 0 && d.least_worn.length === 0);
      })
      .catch(() => setEmpty(true));
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 pt-8 pb-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Analytics</p>
        <h1 className="font-display text-2xl">{empty ? "Nothing to show yet" : "Your closet"}</h1>
      </div>

      {empty && (
        <div className="rounded-lg border border-dashed border-line p-8 text-center">
          <p className="text-sm text-ink-soft">
            Wear stats, cost-per-wear, and rediscovery suggestions show up here once you&apos;ve
            logged a few outfits.
          </p>
        </div>
      )}

      {data && !empty && (
        <>
          <StatRow
            label="Most worn"
            entries={data.most_worn}
            valueLabel={(e) => `${e.times_worn}× worn`}
          />
          <StatRow
            label="Rediscover these"
            entries={data.least_worn}
            valueLabel={(e) => (e.times_worn === 0 ? "never worn" : `${e.times_worn}× worn`)}
          />
          <StatRow
            label="Cost per wear"
            entries={data.cost_per_wear}
            valueLabel={(e) => (e.cost_per_wear ? `$${e.cost_per_wear.toFixed(2)}` : "")}
          />
        </>
      )}
    </main>
  );
}
