// Mirrors app/models/garment.py SENSITIVE_CATEGORIES and database-schema.md's
// `garments.category` enum. Kept as a small shared constant rather than fetched
// from the API — this list changes about as often as the schema itself does.
export const STANDARD_CATEGORIES = [
  "top",
  "bottom",
  "dress",
  "outerwear",
  "shoes",
  "bag",
  "accessory",
  "jewelry",
] as const;

export const SENSITIVE_CATEGORIES = ["underwear", "lingerie"] as const;

export const ALL_CATEGORIES = [...STANDARD_CATEGORIES, ...SENSITIVE_CATEGORIES] as const;

export function isSensitiveCategory(category: string): boolean {
  return (SENSITIVE_CATEGORIES as readonly string[]).includes(category.toLowerCase());
}
