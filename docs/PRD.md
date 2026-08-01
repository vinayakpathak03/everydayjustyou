# Product Requirements Document (PRD)

## Codename: **Muse** — an AI Digital Wardrobe

> "If you're a really pretty girl with really nice clothes, do you need to know what times the buses leave?" — this app is the Clueless closet computer, rebuilt with modern multimodal AI.

Working name for the product throughout this document is **Muse**. Treat it as a placeholder — trivial to rename later since it only appears in copy, not in data models.

---

## 1. Vision

Give someone a digital twin of their entire closet, photographed once, and then let AI do what a personal stylist would: dress them every day, explain its reasoning, track what's actually worn, and help them buy only what they're missing.

The product must *feel* like it was made by Apple — restrained UI, generous whitespace, editorial photography of the clothes themselves as the hero content, fast, quiet, and confident. No clutter, no dashboards-for-dashboards'-sake.

## 1a. Technical Constraints (Locked)

Decided after working through the platform/cost tradeoffs — treated as fixed for the rest of this document, not re-derived per feature. Full reasoning in [tech-stack-justification.md](./tech-stack-justification.md); this is the summary that everything else in this PRD must fit inside.

- **Budget: $0, hard constraint.** Every service below is a genuine free tier, not "cheap." If a feature (§6) seems to need a paid service, the spec calls out the free-tier-compatible substitute instead of quietly assuming a budget.
- **Frontend:** Next.js, shipped as a PWA (installable via Add to Home Screen — no App Store, no Apple Developer account, no Mac required; dev machine is Windows). Target devices: iPhone and iPad.
- **Backend:** FastAPI on Render or Railway free tier. Cold-start delays on wake from idle are an accepted tradeoff, not a bug to fix.
- **Database + Storage + Auth:** Supabase free tier — Postgres with `pgvector` doubles as the vector DB, so no separate vector-DB service.
- **Background removal:** `rembg`, open-source, self-hosted, no per-image cost.
- **AI vision + chat:** Gemini API free tier (not OpenAI — no free tier there). Prompts and call volume are designed to stay within free-tier rate limits for a small, invite-only user base.
- **No Redis / managed queue** — no durable free tier exists for either on Render/Railway; background jobs run through a Postgres-backed job table polled in-process, not a separate worker service.

**This is multi-user, not single-tenant, and not "single household."** The developer, girlfriend, sister, and possibly a few more family members each get their own account (Supabase Auth) and a fully isolated wardrobe, outfits, and chat history — enforced via `user_id` on every relevant table **plus Postgres row-level security**, not just app-level filtering. One user must never be able to see another's data, including by accident (e.g. a bug in a query) — see [database-schema.md §9](./architecture/database-schema.md). **Signup is invite-only**: the developer creates or approves each account; there is no public registration flow. Architected so it could scale further later, without over-building for scale this product doesn't have yet — optimized for "actually works great for the small group using it," not "enterprise-ready."

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
| App becomes a daily habit | DAU/WAU across the invited user group | Opened 5+ days/week per user |
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
16. **Shared/linked closets** (e.g., a couple opting to see into each other's wardrobe, borrow-tracking) — distinct from the multi-user *accounts* already in V1 (§1a): every user already has their own isolated account today; this item is about deliberately, mutually opting two accounts into partial visibility of each other's data, which is a materially different (and currently unbuilt) feature. See PRD §10 candidate #2 for the scoped-down "private circle" version of this idea.

### Explicitly out of scope (for now)
- Public social/sharing features (public profiles, following other closets, discovery feeds)
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

### 6.13 Manual Styling Canvas (new)
- As a user, I can build an outfit by hand — drag items from my wardrobe onto a freeform board, layer/resize/reposition them (shirt behind tie, glasses overlapping the collar, bag to the side), duplicate or delete a piece, undo, and save the result as a real outfit.
- This is the manual counterpart to the AI Outfit Generator (6.2) — same underlying `outfits`/`outfit_items` model (`source = manual`), just user-arranged instead of AI-assembled. A saved Canvas outfit is still eligible for scoring, wear-logging, and analytics like any other outfit.
- Rationale: the AI generator is right most of the time but not always — sometimes a user already knows the exact combination they want and just needs a fast way to lay it out and see it as a cohesive image, not a bulleted list.

### 6.14 Dress Me — Quick Shuffle (new)
- A middle ground between full AI generation (6.2) and the freeform Canvas (6.13): browse a grid of eligible items per slot, **pin** any piece to lock it in, then **shuffle** to have the engine re-roll the unlocked slots — using the same compatibility-scoring engine as the Outfit Generator, so shuffles are constrained-random, not noise.
- Layout density toggle (grid / list / single-column) for browsing; a "surprise me" full shuffle re-rolls everything at once.
- Gives users a fast, game-like way to explore combinations they wouldn't have thought to ask the AI for by name, while staying grounded in real compatibility rules.

### 6.15 Wardrobe Composition & Sustainability Analytics (new — extends 6.5)
- Track **acquisition type** per item (new, pre-loved/secondhand, rental, handmade, gifted, undefined) as an optional field at add-time.
- **Wardrobe usage gauge**: % of the closet actually worn in a rolling window (e.g., last 90 days), with a trend delta against the prior window ("You wore 20% more").
- **Composition breakdown**: donut/segment view of the closet by acquisition type (and, filterable, by category) — surfaces things like over-reliance on new purchases vs. pre-loved/rental, which feeds back into the Shopping Assistant's recommendations (nudging toward pre-loved/rental options when that matches the user's stated preference).
- This reframes Closet Analytics from purely descriptive ("here's your data") toward the product's underlying thesis — wear more of what you already own — with a metric the user can watch move over time.

### 6.16 Wardrobe Profile & Stats Header (new)
- A personal (private-by-default — see 6.11's privacy note and §7 NFRs) stats header atop the Wardrobe: item / outfit / moodboard counts, quick-jump category rail, favorites and archived filters.
- Purely a richer presentation of data the app already has (`garments`, `outfits`, `moodboards` counts) — no new backend surface beyond existing aggregate queries; it exists so the wardrobe *feels* like a curated personal collection the moment you open it, not just a grid.

## 7. Non-Functional Requirements

- **Mobile-first**: primary usage is a phone, one-handed, often while getting dressed. Design for thumb reach, camera-first flows.
- **Performance**: wardrobe grid must stay smooth at 500+ items (virtualized lists, paginated/infinite scroll, image CDN with responsive sizes).
- **Privacy**: this is deeply personal data (a full inventory of someone's body/appearance-adjacent data + photos), owned by multiple separate real people, not one household. Private by default and **isolated by default** — see §7.1 and §1a; no data sharing between accounts without explicit, mutual opt-in (none built in V1 — see §10.1); easy full data export/delete per account.
- **Reliability**: image processing pipeline must be resilient to model failures (including Gemini free-tier rate-limit errors, not just outages) — always fall back to "needs manual tagging" rather than blocking the upload.
- **Scalability**: architecture should comfortably support a handful of invited users with thousands of items each on free-tier infra (§1a), and scale horizontally (paid tiers, more infra) if ever opened beyond that — not designed as if that's imminent.
- **Accessibility**: WCAG AA, since color/pattern description is core content — always pair color swatches with text labels, not color alone.
- **Offline resilience**: viewing an already-loaded wardrobe should degrade gracefully offline (PWA caching); actions queue and sync when back online.

### 7.1 Consent, Privacy & Sensitive Content Policy (firm requirements, not suggestions)

**1. Multi-user data isolation.** Every user gets their own account and a fully isolated wardrobe/outfits/chat history, enforced by `user_id` scoping **and** Postgres row-level security at the database layer — never app-level filtering alone. See [database-schema.md §9](./architecture/database-schema.md) and [system-architecture.md §6](./architecture/system-architecture.md) for the enforcement pattern, including the specific pitfall being guarded against (a backend connecting with Supabase's `service_role` key would silently bypass all of this).

**2. Developer photo access — opt-in, explicit, revocable.** The developer may want a copy of uploaded photos for debugging. This is:
   - Opt-in, **default ON** (pre-checked) — stored as `users.consent_dev_photo_access: boolean`.
   - Presented plainly in the onboarding T&C (tone can be light, the substance must be clear — see §3 below), not buried in a way that defeats the point of asking.
   - Revocable at any time from Settings.

**3. Terms & Conditions — short, developer-voiced, not routed around.** The developer is drafting the actual T&C copy personally, in a fun/personal tone (this is for family, not a public legal document) — not something this spec writes on their behalf. The build requirement is structural: whatever the final copy says, the `consent_dev_photo_access` toggle from item 2 **must live on the same onboarding screen as the T&C text**, not a separate/skippable step — the point is that people actually see and understand what they're agreeing to. The T&C copy must also plainly cover item 4 below (sensitive content) and item 5 (third-party AI disclosure) — content, not just a link to a policy elsewhere.

**4. Sensitive content category — policy-level exclusion, not automated detection.** Free-tier vision models can't reliably distinguish underwear/lingerie/intimate apparel from adjacent categories (tube tops, athletic shorts), so no classifier is built to auto-filter uploads. Instead:
   - The T&C/onboarding copy explicitly asks users not to upload underwear/lingerie photos, since images are otherwise sent to a third-party AI (Gemini) for processing. This is enforced by **disclosed policy**, documented as a known limitation — not a technical guarantee.
   - Items a user *does* flag/mark as a sensitive category (`garments.sensitive_category`) get a stricter, structural path regardless: manual entry only (text description + quantity, photo optional), never sent to Gemini for detection/tagging, no background removal via any third-party call. If a photo is stored at all, it's excluded from outfit-generation views, any shared/social view, and the dev-photo-access pipeline **regardless of that user's `consent_dev_photo_access` setting** — sensitive-category exclusion overrides dev-access consent, never the reverse. See [database-schema.md](./architecture/database-schema.md) `garments.sensitive_category`/`entry_mode`.

**5. Third-party AI data-use transparency.** Onboarding/T&C briefly and honestly discloses that uploaded photos are sent to Google's Gemini API for clothing analysis — not just "we use AI." Per Google's own [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms) (verified for this build, not assumed from general knowledge): on the **free/unpaid tier**, Google may use submitted content and generated responses to improve its products/ML models, and human reviewers may read/annotate input-output pairs (de-identified from the account first); Google's own guidance is "do not submit sensitive, confidential, or personal information to the Unpaid Services" — which is exactly why item 4 exists. (EEA/UK/Switzerland users get the stricter paid-tier data terms even on free usage, per the same source.) Free-tier terms can change; re-verify before the actual T&C copy ships.

**6. Storage bucket permissions — explicitly locked, not assumed.** Supabase Storage buckets are created private with per-user path-scoped access policies, verified against the dashboard as a required Phase 0 setup step — not left at default settings. See [database-schema.md §10](./architecture/database-schema.md).

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
| Gemini free-tier rate limits get hit as more family members are invited / usage grows | Cheapest/fastest Gemini tier for bulk tagging, aggressive caching, rate-limiting inside `AIClient` so bursts degrade to slower processing rather than hard errors (§1a, tech-stack-justification.md) |
| Free-tier hosting cold starts (Render/Railway spin-down) feel sluggish on first open after idle | Accepted tradeoff of the $0 budget, not something engineered away; GitHub Actions cron pings also keep the daily-notification path warm at the right time |
| No Redis/managed queue on free tier — background jobs run in-process | Postgres-backed job table + asyncio poller; documented exit ramp to a real worker+queue if volume ever outgrows this (system-architecture.md §3) |
| Cold-start: empty wardrobe = no value | Strong onboarding flow that gets to 20+ items fast (batch capture mode), sample/demo wardrobe option |
| Virtual try-on is expensive/immature, and V3's try-on model must stay self-hosted/free under the $0 budget | Deferred to V3, MVP substitutes flat-lay collage; free/self-hosted GPU hosting for try-on is an open question deliberately left for V3 |
| A bug in per-user filtering could leak one user's wardrobe to another | Not app-level-only: Postgres RLS enforces isolation at the database layer regardless of query bugs (database-schema.md §9); tested explicitly, not just assumed |

## 10. Proposed Differentiators (USP Candidates)

Everything in §6 closes the gap with existing wardrobe apps. None of it is what would make someone choose *this* app over them. These are candidate differentiators — genuinely distinct angles this product can own, given its actual origin (a personal AI stylist built by one person for another, not a social network chasing DAUs). Flagged for selection before any get a full spec; none are built into the architecture yet except where noted.

1. **A stylist with a voice, not a form.** The AI Stylist (6.4) already exists; the differentiator is giving it a consistent, warm, opinionated *persona* — closer to a real personal stylist's voice than a generic assistant — including optional voice input/output. Competitors have chat features; none commit to a personality. Low technical lift (mostly prompt/system-message design), high perceived-quality payoff.
2. **A private circle of two (or three), not a public feed.** The screenshots that prompted this round show a public social feed (follow, like, share to strangers) — which cuts against this product's actual premise and the privacy commitments already in §7. A scoped-down version fits instead: an **opt-in private circle** (just the couple, maybe a sibling or close friend) where you can leave a note on someone's planned outfit ("wear this for our date"), get gently notified when they're deciding what to wear, or — for the closet-sharing case — see when a trusted person's wardrobe has something that'd complete one of your outfits ("Priya has a blazer like the one your capsule is missing — ask to borrow?"). This is the one item on this list that materially changes the schema and the privacy stance, so it's the one flagged for an explicit decision below rather than assumed.
3. **Contextual memory, used out loud.** The data already exists in `wear_logs`; the differentiator is the AI *proactively* surfacing it: "Last time you interviewed at a company like this, you wore X" or "This time last year, you wore Y for a day like today." Turns a cold database into something that feels like it actually remembers you.
4. **A closet health score you can watch move.** §6.15 gives the raw composition/usage data; the differentiator is compressing it into one number the AI actively coaches toward — closer to a credit-score or sleep-score pattern than a dashboard — with the AI proposing one concrete action per week ("wear the navy blazer once this week and your score goes up 4 points") rather than just reporting stats passively.
5. **A "leaving in 10" check.** A lock-screen widget / time-boxed final nudge — not just a morning notification, but a last-call confirmation a few minutes before the user's usual leave time, cross-referencing the plan against a live weather check in case the forecast shifted since the outfit was chosen.

### 10.1 Default decisions taken (pending confirmation)

Two of the open questions below block real architecture work if left unresolved, so a default was taken rather than stalling — both are easy to override:

- **Social scope → None for V1.** No follow/like/share of other people's closets; the app stays fully private/single-user. This is the option most consistent with the product's actual premise (a personal AI stylist, not a social network) and with the privacy commitments already in §7 — and it's the safer default because loosening privacy later is easy, tightening it after users expect otherwise is not. Candidate #2 above stays documented as a future option, not built.
- **First USP to formalize → #1, Stylist persona/voice.** Lowest technical lift, no schema/privacy implications, and it makes the AI Stylist chat (already core to the MVP) feel distinct from day one. See system-architecture.md §5.3.1 for the resulting spec. The other three USP candidates remain unformalized, ready to spec on request.

## 11. Open Questions for Stakeholder (you)

**Resolved by the locked technical constraints (§1a):**
- ~~Single user vs. shared household wardrobe~~ → **multi-user, invite-only**, each account fully isolated (not a household model at all — see §1a).
- ~~Preferred vision/LLM vendor~~ → **Gemini API free tier**, locked by the $0 budget constraint (OpenAI has no free tier).

**Still open:**
1. Confirm product name (Muse is a placeholder).
2. **Social/community scope** (raised by USP candidate #2 above): defaulted to *None* per §10.1 above — confirm, or redirect toward a private circle or public feed instead.
3. Which of the remaining USP candidates in §10 (contextual memory, closet health score, leaving-in-10 nudge) are worth turning into full specs next? Stylist persona/voice was defaulted to "yes" per §10.1.
4. T&C copy itself — you're drafting this personally; flag when it's ready so the onboarding screen spec (§7.1) can be checked against the actual text.
