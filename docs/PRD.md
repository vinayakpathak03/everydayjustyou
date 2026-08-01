# Product Requirements Document (PRD)

## Codename: **Muse** — an AI Digital Wardrobe

> "If you're a really pretty girl with really nice clothes, do you need to know what times the buses leave?" — this app is the Clueless closet computer, rebuilt with modern multimodal AI.

Working name for the product throughout this document is **Muse**. Treat it as a placeholder — trivial to rename later since it only appears in copy, not in data models.

---

## 1. Vision

Give someone a digital twin of their entire closet, photographed once, and then let AI do what a personal stylist would: dress them every day, explain its reasoning, track what's actually worn, and help them buy only what they're missing.

The product must *feel* like it was made by Apple — restrained UI, generous whitespace, editorial photography of the clothes themselves as the hero content, fast, quiet, and confident. No clutter, no dashboards-for-dashboards'-sake.

## 2. Problem Statement

- People own more clothes than they can hold in their head. They default to the same 20% of their wardrobe ("wear 20%, own 80%").
- Deciding what to wear is a repeated daily cognitive cost (decision fatigue).
- People buy things that don't match what they own because they can't easily "shop their own closet" mentally.
- Packing for trips and dressing for specific occasions (interview, event, weather) is stressful without a system.
- Existing wardrobe apps (Stylebook, Acloset, Whering) are functional but visually dated, manual-entry-heavy, and not conversational/AI-native.

## 3. Target User & Persona

**Primary persona — "Ananya", 27**
- Owns 150–400 clothing items across categories.
- Fashion-conscious, wants outfit inspiration but is time-poor in the morning.
- Comfortable photographing items with her phone; wants the AI to do the tagging.
- Travels a few times a year and wants packing help.
- Wants to shop *intentionally* — not impulse-buy duplicates.

**Secondary persona — the gifting partner (you)**
- Wants to build this *for* someone as a thoughtful, personal, high-craft gift/product.
- Cares about the product feeling premium, private, and delightful to use daily — not a spreadsheet with a chatbot bolted on.

## 4. Goals & Success Metrics

| Goal | Metric | MVP Target |
|---|---|---|
| Wardrobe gets fully digitized | # items catalogued | 150+ items in first 2 weeks |
| Reduces daily decision time | Time from app open → outfit selected | < 60 seconds |
| Outfit suggestions are actually worn | % of AI-suggested outfits marked "worn" | > 30% within first month |
| App becomes a daily habit | DAU/WAU (household of 1–2 users) | Opened 5+ days/week |
| Attribute detection is trustworthy | % of AI-tagged attributes edited by user | < 20% edit rate after v1.1 |
| Analytics changes behavior | Cost-per-wear / rediscovery of "forgotten" items | ≥ 10 previously-unworn items worn in 60 days |

## 5. Scope

### In scope for MVP (V1)
1. AI Wardrobe ingestion (photo → background removal → detection → categorized item)
2. Wardrobe browsing (grid, filters, search, item detail)
3. Outfit Generator (manual "build me an outfit" + scoring + explanation)
4. Basic Smart Recommendations (weather-based)
5. AI Stylist chat (conversational, RAG over wardrobe)
6. Wear logging + basic Closet Analytics (most/least worn, cost-per-wear)
7. Auth, cloud storage, mobile-first responsive web (PWA)

### V2
8. Calendar-aware recommendations, mood/dress-code inputs
9. Packing Assistant
10. Shopping Assistant (gap analysis + matching recommendations)
11. Daily Outfit Notification (push)
12. Capsule wardrobe suggestions, duplicate detection, seasonal rotation

### V3
13. Virtual Try-On (diffusion-based)
14. Fashion Inspiration mode (aesthetic-driven generation: Old Money, Clean Girl, etc.)
15. Native mobile app (React Native/Expo) if usage justifies it
16. Multi-user / shared closets (e.g., couple's shared shoe rack)

### Explicitly out of scope (for now)
- Social/sharing features (public profiles, following other closets)
- Marketplace/resale integration
- Try-on via physical smart mirror / IoT hardware
- Multi-tenant B2B (styling-as-a-service for many clients) — architecture should not preclude it later, but it's not a v1 requirement

## 6. Core Features — Detailed Requirements

### 6.1 AI Wardrobe
**User stories**
- As a user, I can photograph or upload a clothing item and have it automatically background-removed, categorized, and tagged.
- As a user, I can attach multiple photos to one item (front, back, detail, worn-on-body).
- As a user, I can review and correct any AI-assigned attribute before saving.
- As a user, I can browse my wardrobe as a clean grid, filterable by category, color, season, occasion, brand.

**Acceptance criteria**
- Upload → processed, categorized item ready for review in < 15s (async, with optimistic UI showing "processing" state).
- Detected attributes: category, subcategory, primary/secondary color, pattern, fabric guess, sleeve length, neckline, fit, season(s), occasion(s), formality score.
- Background removed to transparent PNG, item shot on a consistent neutral canvas in the UI (echoing the Clueless closet-computer flatlay aesthetic).
- If multiple garments are visible in one photo (e.g., a full outfit photo), the system detects and offers to split into multiple items (V2 stretch; V1 can require single-item photos with a light "we noticed more than one item — want to split this?" nudge).

### 6.2 Outfit Generator
- Generate N outfit options from existing items only (no phantom items).
- Each outfit includes: top-level layer(s), bottom or dress, shoes, bag, accessories/jewelry as appropriate.
- Score 1–100 with a breakdown (color harmony, occasion fit, weather fit, formality consistency, novelty/rediscovery bonus).
- Natural-language explanation ("Why this works": e.g., "The sage trench and cream trousers are a tonal, low-contrast pairing that reads polished without trying hard; the loafers keep it grounded for daytime.")
- "Show me alternatives" swaps one slot (e.g., different shoes) while holding the rest constant, and re-scores.

### 6.3 Smart Recommendations
- Inputs, each optional and composable: weather (auto via geolocation), calendar event (if connected), time of day, dress code (free text or preset), mood (preset chips: confident, cozy, playful, powerful...), color preference, travel destination.
- Output: ranked outfit suggestions with the same scoring/explanation model as 6.2, just with additional context weighting.

### 6.4 AI Stylist (conversational)
- Free-text chat, wardrobe-grounded via RAG (semantic + structured filtering over the user's actual items — never invents items).
- Tool-using: the assistant can call `search_wardrobe`, `get_weather`, `get_calendar_events`, `generate_outfit`, `log_wear`, `get_wear_history` as function-calling tools.
- Must handle the example prompts verbatim from the brief: "What should I wear for dinner?", "I have a job interview", "I want something cute but comfortable", "I wore this yesterday" (should exclude/deprioritize recently-worn items), "Show me pink outfits" (color-filtered gallery response, not just prose).
- Chat responses can render rich cards (outfit previews), not just text.

### 6.5 Closet Analytics
- Most/least worn items (by count and by recency).
- Cost-per-wear = purchase price / times worn (requires optional price + purchase date fields).
- Capsule wardrobe suggestions (cluster analysis over color/category to propose a minimal high-coverage subset).
- Missing essentials (rule-based + LLM-assisted gap detection against a configurable "essentials checklist" per style profile).
- Duplicate/near-duplicate detection (embedding similarity above a threshold within the same category).
- Seasonal rotation nudges ("12 summer items haven't been worn since May — pack away or donate?").

### 6.6 Packing Assistant
- Inputs: destination, date range, trip type (business, leisure, beach...).
- Fetches weather forecast for destination/date range (or historical seasonal average if forecast unavailable).
- Outputs a packing list of actual owned items forming N complete outfits + versatility-maximizing extras, with a "why this covers your trip" summary.

### 6.7 Shopping Assistant
- Recommends purchases that plug real gaps (from 6.5) or complete high-scoring outfits that are one item away from great ("You have 4 outfits that would jump 15+ points with a tan crossbody bag").
- Recommendations reference *item archetypes* (attributes) first; a later integration can map to real product search/affiliate APIs — architecture must not hard-couple to one retailer.

### 6.8 Virtual Try-On (V3)
- Visualize a generated outfit on the user's uploaded reference photo/avatar.
- Flagged as high compute cost / high complexity; MVP substitute is a 2D flat-lay collage (already produced by background-removed items composited on a canvas), which is cheap and still very "Clueless closet."

### 6.9 Daily Outfit Notification
- Scheduled job (per-user configurable time) generates 3 outfits using the Smart Recommendations engine with the day's weather + calendar, and delivers via push notification (PWA Web Push, email fallback).

### 6.10 Fashion Inspiration
- Preset aesthetic profiles (Old Money, Clean Girl, Minimalist, Korean Fashion, Streetwear, Quiet Luxury, + user-defined) act as a scoring/style prompt overlay on the Outfit Generator — "give me an outfit from my closet that leans Quiet Luxury."

### 6.11 Moodboards & Inspiration Clipping (new)
- As a user, I can save any outfit/look I find inspiring — from the web, a screenshot, a Pinterest-style share, or a photo of a friend — into named boards ("Party", "Office", "Summer", "Bday wishes").
- As a user, each saved clip can be AI-matched against my own wardrobe: "You already own something like the boots in this photo" / "3 items in your closet would recreate 70% of this look."
- Boards are a distinct surface from AI-generated Fashion Inspiration (6.10) — 6.10 is AI-generated *from your closet*; 6.11 is *user-curated reference material* the AI can draw on when generating (e.g., "style me like my Party board tonight").
- Ingestion: paste a URL/share-sheet share, or upload a screenshot — the same vision pipeline (§5.1 in system-architecture.md) extracts a description + embedding from the clip so it's searchable and matchable, exactly like a garment, but stored as `inspiration_items` rather than `garments` (it's a reference image, not an owned item).

### 6.12 Weekly Planner (new)
- As a user, I can see my week as a calendar strip (Sun–Sat) and assign a planned outfit to specific upcoming days — not just "today," a real look-ahead view.
- Each day shows weather + a thumbnail of the planned outfit (or a prompt to plan one) at a glance.
- Distinct from the Daily Outfit Notification (6.9), which is a single-day AI push; the Weekly Planner is the user-driven, editable calendar surface that the notification and Smart Recommendations both read from and write into — planning Tuesday's outfit on Sunday should mean Tuesday's notification reflects that choice rather than generating a fresh one.
- Drag/tap to reassign an outfit to a different day; conflicts (same outfit planned twice in a short window) get a gentle "you're repeating this soon" nudge, tying into Closet Analytics' novelty scoring (6.2).

## 7. Non-Functional Requirements

- **Mobile-first**: primary usage is a phone, one-handed, often while getting dressed. Design for thumb reach, camera-first flows.
- **Performance**: wardrobe grid must stay smooth at 500+ items (virtualized lists, paginated/infinite scroll, image CDN with responsive sizes).
- **Privacy**: this is deeply personal data (a full inventory of someone's body/appearance-adjacent data + photos). Private by default, no data sharing/training opt-in without explicit consent, easy full data export/delete.
- **Reliability**: image processing pipeline must be resilient to model failures — always fall back to "needs manual tagging" rather than blocking the upload.
- **Scalability**: architecture should comfortably support a single household's wardrobe (thousands of items) on V1 infra, and scale horizontally if opened to more users later.
- **Accessibility**: WCAG AA, since color/pattern description is core content — always pair color swatches with text labels, not color alone.
- **Offline resilience**: viewing an already-loaded wardrobe should degrade gracefully offline (PWA caching); actions queue and sync when back online.

## 8. Design Principles (Apple-inspired)

1. **The clothes are the UI.** Large, clean product photography (post background-removal) is the primary visual language — think App Store "Today" cards, not spreadsheet rows.
2. **Restraint over density.** One primary action per screen. Progressive disclosure for attributes/filters.
3. **Motion with purpose.** Subtle spring transitions (card expand → detail), never decorative for its own sake.
4. **Typography-led hierarchy.** A single confident type family (system font stack: SF Pro on Apple devices, Inter fallback), generous line-height, no more than 2 weights per screen.
5. **Neutral canvas, color pops from the clothes.** Backgrounds are near-white/near-black (light/dark mode); the wardrobe's own colors provide visual richness.
6. **Native-feeling gestures.** Swipe to like/skip an outfit suggestion (Tinder-for-outfits pattern), long-press for quick actions, haptics on supported devices.

### 8.1 Visual Identity — Palette

Principle 5 ("neutral canvas, color pops from the clothes") holds; the *color* of that canvas and accents is now specified as a **Barbie-land-inspired palette** rather than the neutral sage/camel direction sketched earlier, giving the product a warmer, more playful "cute & girly" register while keeping the same restrained, one-accent-at-a-time layout discipline:

| Token | Hex | Use |
|---|---|---|
| Lilac | `#CDB4DA` | secondary accent — chips, secondary CTAs, planner highlights |
| Blush | `#FFC8DC` | tint backgrounds, low-emphasis surfaces |
| Pink | `#FFAFCC` | garment-card placeholder tint, board covers |
| Magenta | `#E55E99` | primary accent — score badges, primary CTA, active states |
| Orchid | `#EBB9DF` | tertiary tint, hover/pressed states |

Canvas stays near-white (warm, faintly pink-tinted) in light mode and near-black (warm, faintly plum-tinted) in dark mode — the palette above is for accents and small surfaces, not for flooding the background, so the clothing photography still reads as the richest color on any screen. See the wireframes artifact for the palette applied to real UI.

## 9. Risks & Assumptions

| Risk | Mitigation |
|---|---|
| Vision model mis-tags attributes (esp. fabric, which is hard from photos alone) | Always editable, show confidence, treat fabric/pattern as "best guess" not ground truth |
| GPT/vision API costs scale with wardrobe size and chat usage | Cache aggressively, use cheaper models for bulk classification, reserve top-tier models for chat reasoning |
| Cold-start: empty wardrobe = no value | Strong onboarding flow that gets to 20+ items fast (batch capture mode), sample/demo wardrobe option |
| Virtual try-on is expensive/immature | Deferred to V3, MVP substitutes flat-lay collage |
| Single-household scope today, but should this ever become multi-tenant? | Schema is user_id-scoped from day one so multi-tenancy is additive, not a rewrite |

## 10. Open Questions for Stakeholder (you)

1. Confirm product name (Muse is a placeholder).
2. Single user vs. shared household wardrobe in V1 (schema supports either; recommend single-owner-per-item with optional household grouping later).
3. Preferred vision/LLM vendor split — brief says OpenAI GPT; confirm if Anthropic Claude is acceptable as an alternate/secondary vision-and-reasoning provider (useful for cost/redundancy).
