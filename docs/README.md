# Muse — AI Digital Wardrobe: Architecture & Planning Docs

Full architecture and planning set for the AI-powered digital wardrobe assistant (Clueless-closet-computer, rebuilt with modern multimodal AI). **No application code has been written yet** — per the brief, this documentation set is the finalized architecture the implementation will follow.

## Reading order

1. **[PRD.md](./PRD.md)** — Vision, personas, goals/metrics, full feature requirements (all 10 core features), non-functional requirements, design principles, scope (V1/V2/V3), risks.
2. **[architecture/system-architecture.md](./architecture/system-architecture.md)** — High-level system diagram, component responsibilities, deployment topology, and the detailed AI architecture (ingestion pipeline, outfit generation engine, AI Stylist RAG/tool-calling, embeddings, virtual try-on, cost controls).
3. **[architecture/database-schema.md](./architecture/database-schema.md)** — Full PostgreSQL schema (ERD + table-by-table columns), including `pgvector` usage.
4. **[architecture/api-architecture.md](./architecture/api-architecture.md)** — FastAPI router map, key endpoint contracts, internal service boundaries, streaming/real-time, auth.
5. **[architecture/folder-structure.md](./architecture/folder-structure.md)** — Monorepo layout for the web app, API, AI worker, and shared packages.
6. **[design/user-flows.md](./design/user-flows.md)** — Mermaid flowcharts for the 9 core user journeys (onboarding, add-item, outfit generation, Stylist chat, daily notification, packing, analytics, shopping, inspiration).
7. **[design/ui-wireframes.md](./design/ui-wireframes.md)** — Screen-by-screen wireframe descriptions and design language (Barbie-land palette). Companion visual artifact (lo-fi mockups of all 13 core screens) was published separately in the chat session.
8. **[roadmap/roadmap-and-sprints.md](./roadmap/roadmap-and-sprints.md)** — 7-phase roadmap, sprint-by-sprint breakdown, MVP vs. feature-complete milestones, team allocation.
9. **[tech-stack-justification.md](./tech-stack-justification.md)** — Every technology choice with the tradeoff made explicit, and what was deliberately *not* chosen.

## Snapshot

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind, mobile-first PWA
- **Backend:** FastAPI (Python, async), modular monolith + separate AI worker service
- **Database:** PostgreSQL + `pgvector` (Supabase)
- **AI:** GPT-4o (vision + chat + reasoning), `rembg` for background removal, CLIP + text embeddings for semantic search, hybrid rule-based + LLM outfit scoring engine
- **Storage/Auth:** Cloudflare R2/Supabase Storage, Supabase Auth
- **MVP milestone:** end of Phase 2 (AI Wardrobe + Outfit Generator + basic Analytics) — see roadmap
- **Full brief coverage** (minus Virtual Try-On): end of Phase 5

## Open decisions

See PRD §10 — product naming, single-user vs. shared-household wardrobe scope, and confirming OpenAI vs. a mixed OpenAI/Anthropic provider strategy are flagged for stakeholder input before Phase 0 kicks off.
