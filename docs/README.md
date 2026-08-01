# Muse — AI Digital Wardrobe: Architecture & Planning Docs

Full architecture and planning set for the AI-powered digital wardrobe assistant (Clueless-closet-computer, rebuilt with modern multimodal AI). **No application code has been written yet** — this documentation set is the finalized architecture the implementation will follow, built to a **hard $0 budget** against a locked stack, and designed as a **multi-user, invite-only** product (developer + a handful of family members, each with a fully isolated account) from day one — see PRD §1a.

## Reading order

1. **[PRD.md](./PRD.md)** — Vision, personas, goals/metrics, full feature requirements (all 10 core features), non-functional requirements, design principles, scope (V1/V2/V3), risks.
2. **[architecture/system-architecture.md](./architecture/system-architecture.md)** — High-level system diagram, component responsibilities, deployment topology, and the detailed AI architecture (ingestion pipeline, outfit generation engine, AI Stylist RAG/tool-calling, embeddings, virtual try-on, cost controls).
3. **[architecture/database-schema.md](./architecture/database-schema.md)** — Full PostgreSQL schema (ERD + table-by-table columns), including `pgvector` usage.
4. **[architecture/api-architecture.md](./architecture/api-architecture.md)** — FastAPI router map, key endpoint contracts, internal service boundaries, streaming/real-time, auth.
5. **[architecture/folder-structure.md](./architecture/folder-structure.md)** — Monorepo layout for the web app, API, AI worker, and shared packages.
6. **[design/user-flows.md](./design/user-flows.md)** — Mermaid flowcharts for the 9 core user journeys (onboarding, add-item, outfit generation, Stylist chat, daily notification, packing, analytics, shopping, inspiration).
7. **[design/ui-wireframes.md](./design/ui-wireframes.md)** — Screen-by-screen wireframe descriptions and design language (Barbie-land palette). Companion visual artifact (lo-fi mockups of all 17 core screens, including the invite-only onboarding/consent screen, sensitive-item manual entry, the Styling Canvas, and Dress Me shuffle) was published separately in the chat session.
8. **[roadmap/roadmap-and-sprints.md](./roadmap/roadmap-and-sprints.md)** — 7-phase roadmap, sprint-by-sprint breakdown, MVP vs. feature-complete milestones, team allocation.
9. **[tech-stack-justification.md](./tech-stack-justification.md)** — Every technology choice with the tradeoff made explicit, and what was deliberately *not* chosen.

## Snapshot

- **Budget:** $0, hard constraint — every service below is a genuine free tier (see [tech-stack-justification.md](./tech-stack-justification.md))
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind, mobile-first PWA (iPhone/iPad via Add to Home Screen — no App Store)
- **Backend:** FastAPI (Python, async), single deployable on Render/Railway free tier — no separate worker service, no Redis
- **Database + Storage + Auth:** Supabase free tier — PostgreSQL + `pgvector`, private per-user-scoped Storage buckets, invite-only Auth
- **AI:** Gemini API free tier (vision + chat + reasoning + embeddings), `rembg` + CLIP self-hosted, hybrid rule-based + LLM outfit scoring engine
- **Multi-user isolation:** every account fully isolated via `user_id` + Postgres Row-Level Security, enforced at the database layer, not just app code — see [architecture/database-schema.md §9](./architecture/database-schema.md)
- **MVP milestone:** end of Phase 2 (AI Wardrobe + Outfit Generator + basic Analytics) — see roadmap
- **Full brief coverage** (minus Virtual Try-On): end of Phase 5

## Open decisions

See PRD §11 — product naming and the remaining USP candidates to formalize are flagged for stakeholder input. Wardrobe scope (multi-user, invite-only) and AI vendor (Gemini, free tier) are **resolved**, locked by the $0 technical constraints in PRD §1a — not open questions anymore.
