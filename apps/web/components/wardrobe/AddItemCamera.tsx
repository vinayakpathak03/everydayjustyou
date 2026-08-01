"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch, apiUpload, subscribeToGarmentEvents } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";

type UploadResponse = { garment_id: string; image_id: string; status: string };
type GarmentDetail = {
  id: string;
  category: string;
  primary_color: string | null;
  pattern: string | null;
  season: string[] | null;
  occasion: string[] | null;
  ai_description: string | null;
  status: string;
  images: { id: string; storage_url: string; is_primary: boolean }[];
};

type Stage = "capture" | "uploading" | "processing" | "review" | "error";

export function AddItemCamera() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [stage, setStage] = useState<Stage>("capture");
  const [imageId, setImageId] = useState<string | null>(null);
  const [garment, setGarment] = useState<GarmentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (stage !== "processing" || !imageId) return;
    const unsubscribe = subscribeToGarmentEvents((event) => {
      if (event.image_id !== imageId) return;
      if (event.status === "tagged" || event.status === "needs_review") {
        apiFetch<GarmentDetail>(`/garments/${event.garment_id}`)
          .then((g) => {
            setGarment(g);
            setStage("review");
          })
          .catch(() => setError("Processing finished but couldn't load the result."));
      }
    });
    return unsubscribe;
  }, [stage, imageId]);

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setStage("uploading");
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiUpload<UploadResponse>("/garments/images", formData);
      setImageId(res.image_id);
      setStage("processing");
    } catch {
      setError("Upload failed — check your connection and try again.");
      setStage("error");
    }
  }

  async function handleSaveReview() {
    if (!garment) return;
    router.push(`/wardrobe/${garment.id}`);
  }

  if (stage === "capture" || stage === "error") {
    return (
      <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
            {searchParams.get("category") ?? "Item"}
          </p>
          <h1 className="font-display text-2xl">Take a photo</h1>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleFileSelected}
        />
        <Button onClick={() => fileInputRef.current?.click()}>Open camera</Button>
        {error && <p className="text-xs text-accent">{error}</p>}
      </main>
    );
  }

  if (stage === "uploading" || stage === "processing") {
    return (
      <main className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center gap-4 px-6 text-center">
        <div className="h-40 w-32 animate-pulse rounded-lg bg-secondary-soft" />
        <p className="text-sm text-ink-soft">
          {stage === "uploading" ? "Uploading..." : "Working on it — background removal + tagging"}
        </p>
      </main>
    );
  }

  // review
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col gap-4 px-6 py-8">
      <h1 className="font-display text-2xl">Looks right?</h1>
      {garment?.images[0] && (
        // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL, not a Next-optimizable static asset
        <img
          src={garment.images[0].storage_url}
          alt=""
          className="h-64 w-full rounded-lg object-contain bg-secondary-soft"
        />
      )}
      <div className="flex flex-wrap gap-2">
        {garment?.category && <Chip active>{garment.category}</Chip>}
        {garment?.primary_color && <Chip>{garment.primary_color}</Chip>}
        {garment?.pattern && <Chip>{garment.pattern}</Chip>}
        {garment?.occasion?.map((o) => <Chip key={o}>{o}</Chip>)}
      </div>
      {garment?.ai_description && (
        <p className="text-sm text-ink-soft">{garment.ai_description}</p>
      )}
      <p className="text-xs text-ink-faint">
        Full attribute editing lands with the item detail screen — for now, save as-is.
      </p>
      <Button onClick={handleSaveReview}>Looks good — save</Button>
    </main>
  );
}
