"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";

// Sensitive-category manual entry (wireframes screen 3a). No camera-first prompt,
// no photo required — this path never touches rembg or Gemini. See PRD §7.1 item 4.
export function AddItemManual() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const category = searchParams.get("category") ?? "underwear";

  const [description, setDescription] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch("/garments/manual", {
        method: "POST",
        body: JSON.stringify({
          category,
          manual_description: description,
          manual_quantity: quantity,
          sensitive_category: true,
        }),
      });
      router.push("/wardrobe");
    } catch {
      setError("Couldn't save — check your connection and try again.");
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col gap-4 px-6 py-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint capitalize">
          {category}
        </p>
        <h1 className="font-display text-2xl">Quick text entry</h1>
        <p className="mt-1 text-xs text-ink-soft">
          Skipping AI tagging for this one — it stays out of outfit suggestions and photo
          processing entirely.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="description" className="font-mono text-xs text-ink-soft">
            Description
          </label>
          <input
            id="description"
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. black cotton briefs"
            className="rounded-md border border-line bg-bg-elevated px-3 py-2 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="quantity" className="font-mono text-xs text-ink-soft">
            Quantity
          </label>
          <input
            id="quantity"
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            className="rounded-md border border-line bg-bg-elevated px-3 py-2 text-sm"
          />
        </div>
        {error && <p className="text-xs text-accent">{error}</p>}
        <Button type="submit" disabled={submitting || !description}>
          {submitting ? "Saving..." : "Save item"}
        </Button>
      </form>
    </main>
  );
}
