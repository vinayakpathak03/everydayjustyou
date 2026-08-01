# Implementation Roadmap & Sprint Planning

Assumes a small build team (1–2 full-stack/AI engineers + AI-assisted development, e.g. Claude Code) and 2-week sprints. Adjust pacing to actual team size — the phase *order* is the important constraint, since each phase's data (garments, wear logs) is what the next phase's AI features reason over.

## Phase Overview

| Phase | Theme | Sprints | Ships |
|---|---|---|---|
| 0 | Foundations | 1–2 | Auth, infra, design system, empty-state app shell |
| 1 | AI Wardrobe (MVP core) | 3–5 | Photo → catalogued item, wardrobe grid |
| 2 | Outfit Generator + basic Analytics | 6–7 | Scored outfit suggestions, wear logging |
| 3 | AI Stylist + Smart Recommendations | 8–9 | Conversational chat, weather/calendar context |
| 4 | Packing + Shopping Assistants | 10–11 | Trip packing lists, gap-based shopping recs |
| 5 | Daily Notification + Weekly Planner + Moodboards + Fashion Inspiration + full Analytics | 12–14 | Push notifications, week-ahead planning, inspiration clipping, aesthetic presets, capsule/duplicate/rotation insights |
| 6 | Virtual Try-On + Polish + Scale | 15–17 | Flat-lay/try-on visualization, performance hardening |

**MVP launch (usable daily) = end of Phase 2. Feature-complete against the brief = end of Phase 5.** Phase 6 is explicitly the highest-risk, lowest-certainty phase and is treated as a stretch/iterate-later phase.

---

## Phase 0 — Foundations (Sprints 1–2)

**Sprint 1: Infra & Auth**
- Monorepo scaffold (per [folder-structure.md](../architecture/folder-structure.md)).
- Postgres + pgvector provisioned (Supabase), docker-compose for local dev.
- Auth integrated (Supabase Auth): sign up/in, session handling in Next.js + FastAPI JWT validation.
- CI pipeline: lint, typecheck, test, preview deploy.
- Object storage bucket + signed upload URLs wired end-to-end (upload a raw file, confirm it lands in storage).

**Sprint 2: Design system & app shell**
- Design tokens (color/type/spacing per [ui-wireframes.md](../design/ui-wireframes.md)) implemented in Tailwind config.
- Core UI primitives: Button, Card, Sheet, Chip, Tab bar, Score badge.
- App shell: bottom tab navigation, onboarding flow skeleton (screens only, no AI yet).
- PWA manifest + service worker scaffold (installable, no offline logic yet).

*Exit criteria: a signed-in user can navigate an empty app shell across all tabs on a phone.*

---

## Phase 1 — AI Wardrobe Core (Sprints 3–5)

**Sprint 3: Ingestion pipeline (backend)**
- `garments`, `garment_images`, `garment_embeddings` tables + migrations.
- Redis queue + worker service scaffold; background-removal job (`rembg`) working end-to-end.
- Vision attribute-extraction job (structured GPT-4o/Claude call) with the JSON contract from [system-architecture.md §5.1](../architecture/system-architecture.md).
- SSE endpoint for upload status.

**Sprint 4: Add-item & review flow (frontend)**
- Camera-first capture screen, multi-photo support.
- Optimistic "processing" card → live status update via SSE.
- Attribute review sheet (editable chips, confidence-aware highlighting).
- Save/correct → persists to `garments`.

**Sprint 5: Wardrobe browse**
- Wardrobe grid with category filters, color/season/occasion filters, search (structured first, semantic search wired once embeddings are populated).
- Item detail screen.
- Batch-capture onboarding flow (get to 10–20 items in first session).

*Exit criteria: a real wardrobe (50+ items) can be photographed, auto-tagged, corrected, and browsed. This is the demo-able MVP milestone.*

---

## Phase 2 — Outfit Generator & Basic Analytics (Sprints 6–7)

**Sprint 6: Outfit generation engine**
- Candidate retrieval + rule-based compatibility scoring (color harmony, formality, season/weather fit).
- LLM re-ranking + rationale generation over top-K candidates.
- `outfits`/`outfit_items` persistence, `/outfits/generate` endpoint.
- Outfit result UI (swipeable cards, score badge, detail view, slot-swap "alternatives").

**Sprint 7: Wear logging + core analytics**
- `wear_logs` + "Wear this today" action from outfit detail/Home.
- `garment_wear_stats` materialized view.
- Analytics screen v1: most/least worn, cost-per-wear.
- Home ("Today") screen wired to real generated outfits (weather-only context for now).

*Exit criteria: user gets a real scored outfit suggestion from their own closet, can act on it, and sees it reflected in wear stats.*

---

## Phase 3 — AI Stylist & Smart Recommendations (Sprints 8–9)

**Sprint 8: Stylist chat backend**
- Tool-calling loop (`search_wardrobe`, `get_weather`, `generate_outfit`, `log_wear`, `get_wear_history`).
- `chat_conversations`/`chat_messages`, SSE streaming endpoint.
- Weather integration (OpenWeatherMap) + `weather_cache`.

**Sprint 9: Stylist chat UI + calendar context**
- Chat UI with inline outfit cards, suggested-prompt chips.
- Google Calendar connect flow (read-only), `get_calendar_events` tool + dress-code inference from event titles.
- Mood/color/occasion context sheet wired into `/outfits/generate`.
- Style profile (`style_profiles`) capture in onboarding + settings, injected into chat system context.

*Exit criteria: the example prompts from the PRD ("What should I wear for dinner?", "I have a job interview", "Show me pink outfits", "I wore this yesterday") all work correctly end-to-end.*

---

## Phase 4 — Packing & Shopping Assistants (Sprints 10–11)

**Sprint 10: Packing Assistant**
- `packing_lists`/`packing_list_items`, destination weather forecast lookup.
- Outfit-grouped packing list generation (reuses Outfit Generation Engine with trip context).
- Packing checklist UI.

**Sprint 11: Shopping Assistant**
- Gap-detection logic (missing essentials + outfit-completion analysis) as part of `AnalyticsService`.
- `shopping_recommendations` generation + dismiss/purchased actions.
- Shopping UI (archetype cards, "unlocks these outfits" framing).
- "Mark purchased" → loops back into add-item flow once the item arrives.

*Exit criteria: user can plan a trip end-to-end and receive at least one genuinely useful purchase recommendation grounded in real wardrobe gaps.*

---

## Phase 5 — Notifications, Planner, Moodboards, Inspiration & Full Analytics (Sprints 12–14)

**Sprint 12: Daily notification + Weekly Planner**
- Scheduled job: per-user daily outfit generation + Web Push delivery (VAPID), email fallback.
- `outfit_plans` table + `/planner` endpoints; notification job checks for a user-set plan before generating a fresh suggestion (a planned outfit always takes precedence).
- Weekly Planner UI (day strip, plan/reassign flow, repeat-nudge tied into novelty scoring).
- Notification settings (time picker) in Settings.

**Sprint 13: Moodboards & full analytics**
- `moodboards`/`moodboard_items`/`inspiration_matches` tables; clip ingestion reuses the vision/embedding pipeline from Phase 1.
- Wardrobe-match computation (embedding similarity between a clip and owned garments) + "style me like this board" hand-off into the generator/Stylist.
- Analytics v2: capsule wardrobe suggestions, duplicate detection (embedding similarity), seasonal rotation nudges.

**Sprint 14: Fashion Inspiration**
- Aesthetic preset definitions (Old Money, Clean Girl, Minimalist, Korean Fashion, Streetwear, Quiet Luxury) as scoring-bias overlays on the generation engine.
- Inspiration tab UI (preset grid + custom "describe a vibe" input).

*Exit criteria: every feature in the original brief except Virtual Try-On is live and used daily, including the Moodboard and Weekly Planner additions.*

---

## Phase 6 — Virtual Try-On, Polish & Scale (Sprints 15–17)

**Sprint 15: Flat-lay collage (interim try-on)**
- Canvas-based compositing of background-removed items into a styled flat-lay image, cached per outfit (`collage_image_url`).

**Sprint 16: Virtual Try-On (stretch)**
- Evaluate hosted vs. self-hosted diffusion garment-transfer model (OOTDiffusion/IDM-VTON or a hosted vendor) against cost/latency/quality; ship behind a feature flag given cost uncertainty.

**Sprint 17: Performance, polish, hardening**
- Wardrobe grid virtualization/performance pass at 500+ items.
- Offline PWA caching pass.
- Accessibility audit (WCAG AA).
- Cost/observability dashboard for AI spend (Sentry + usage logging via `AIClient`).
- Full data export/delete flow (privacy commitment from the PRD).

---

## Suggested Team Allocation

| Role | Focus |
|---|---|
| Full-stack engineer | Next.js frontend, FastAPI routers/services, deployment |
| AI/backend engineer | Worker pipeline, prompt design, outfit-scoring engine, RAG/tool-calling |
| Design (part-time/self-served via this doc set) | Wireframe fidelity increases as real garment photography becomes available |

A solo builder using AI-assisted coding (e.g., Claude Code) can realistically compress this to roughly the same phase *order* but fewer, longer sprints — the sequencing (ingestion → generation → chat → auxiliary features → try-on) is the part that shouldn't be reordered, since each phase depends on data/infrastructure the previous one produced.
