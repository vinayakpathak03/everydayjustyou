import type { MetadataRoute } from "next";

// Next.js App Router's built-in manifest route — served at /manifest.webmanifest.
// This is what makes "Add to Home Screen" work on iPhone/iPad without an App
// Store listing. Icon files themselves aren't checked in yet (placeholder paths) —
// swap in real exported icons before shipping; the PWA still installs without
// them, just with a generic icon.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Muse — AI Digital Wardrobe",
    short_name: "Muse",
    description: "Your closet, digitized. AI-styled outfits from what you already own.",
    start_url: "/today",
    display: "standalone",
    background_color: "#fbf6f8",
    theme_color: "#e55e99",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
