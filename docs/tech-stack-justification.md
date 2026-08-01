# Tech Stack Justification

Every choice below is scoped to the brief's required stack (React/Next.js, FastAPI, PostgreSQL, Python AI services, OpenAI GPT, vision model, background removal, vector DB, cloud storage, auth) and picks a *specific* implementation within each, with the tradeoff made explicit.

## Frontend

**Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui-style primitives + Framer Motion**
- Required by the brief (React); Next.js adds SSR/streaming for fast first paint (important for a "premium/fast" feel), file-based routing that maps cleanly to the screen list, and native Vercel deployment with image optimization (matters a lot for a photo-heavy app).
- Tailwind + a small owned component layer (rather than a heavy component library) keeps the Apple-like restraint achievable — utility CSS makes a strict spacing/type scale easy to enforce project-wide.
- Framer Motion for the small set of purposeful transitions (card → detail, swipe stack) called for in the design principles — used sparingly, not as a default.
- **PWA, not native app, for V1.** Installable, push-capable (Web Push/VAPID), camera-capable via `<input capture>`/`getUserMedia`, one codebase. A React Native app is deferred to V3 — justified only once usage data shows native-specific needs (e.g., deeper camera control, widget/lock-screen presence) that the PWA can't meet.

## Backend

**FastAPI (Python, async)**
- Required by the brief. Async-native (matters for I/O-bound work: DB, storage, external AI calls), Pydantic gives typed request/response validation "for free," and auto-generated OpenAPI spec feeds the frontend's generated TypeScript client (`packages/types`) — contract drift between frontend/backend becomes a build-time problem, not a runtime one.
- Python is also the natural home for the AI/vision workloads, so the API and AI worker share one language and can share service-layer code (see [folder-structure.md](./architecture/folder-structure.md)) instead of maintaining two stacks.

**Modular monolith + separate worker service** (not full microservices)
- A small build doesn't benefit from microservice operational overhead yet. The one real scaling-axis split that *does* matter early — request/response API vs. bursty CPU/GPU-bound AI jobs — is already separated (see [system-architecture.md §3](./architecture/system-architecture.md)), which is the seam that would actually need independent scaling first.

## Database

**PostgreSQL + `pgvector` extension** (via Supabase, or AWS RDS)
- Required by the brief for the relational store; `pgvector` lets the *same* database serve as the vector DB for embeddings at this scale (a wardrobe is hundreds to low-thousands of items per user — nowhere near where a dedicated vector DB like Pinecone/Weaviate/Qdrant earns its operational cost).
- One database means one backup story, one migration tool (Alembic), one place to reason about consistency (e.g., a wear-log write and its materialized-view refresh).
- Explicit exit ramp: the embeddings table is accessed only through an `EmbeddingStore` interface (never queried ad hoc elsewhere), so lifting it out to a dedicated vector DB later — if the product ever opens beyond a household to many users — is a swap behind that interface, not a rewrite.
- **Supabase specifically** (recommended over raw RDS) bundles Postgres + pgvector + Storage + Auth under one vendor, which meaningfully reduces ops burden for a small/solo build. Trade-off: some vendor lock-in; mitigated by keeping storage/auth behind thin client interfaces (`StorageClient`, auth dependency) so a future migration to AWS-native services is a swap, not a rewrite.

## AI / Vision

**OpenAI GPT-4o (primary) for chat reasoning, structured attribute extraction, and outfit rationale generation**
- Required by the brief. GPT-4o's multimodal (vision) input handles the clothing-attribute-extraction task in the same call as the text reasoning, avoiding a separate custom-trained image classifier — which would need labeled fashion training data unavailable at "one wardrobe" scale. Function/tool calling is what makes the Stylist chat reliably resolve "I have a job interview" into a real `generate_outfit(...)` call rather than free-text guessing.
- **Provider abstraction (`AIClient`)** is a deliberate architectural choice, not just the brief's requirement — it lets a cheaper/faster model handle bulk background tagging while a stronger model handles interactive chat, and leaves room to add Anthropic Claude (also multimodal) as a secondary/fallback provider for cost or redundancy without touching calling code. Anthropic is not a strict requirement here, but the abstraction makes it a config change, not an architecture change.

**Background removal: `rembg` (U2Net/ISNet), self-hosted in the AI worker**
- Open-source, no per-image API cost, runs fine on CPU (GPU optional for throughput), and this exact task (clean product-style background removal) is well within its accuracy envelope — no need for a paid API (e.g., remove.bg) at personal-wardrobe volume. The worker abstracts this behind a `BackgroundRemover` interface so swapping to a hosted API later (e.g., if quality on tricky fabrics/patterns disappoints) is a one-file change.

**Embeddings: CLIP (image) + OpenAI `text-embedding-3-small` (text description)**
- CLIP gives visual similarity (duplicate detection, "items that look like this") without needing the LLM in the loop for every search. Text embeddings over the AI-generated description power the Stylist's semantic search ("something flowy for a beach dinner") where the query is conceptual, not visual.

## Storage, Notifications, Integrations

**Cloud image storage: Cloudflare R2 or Supabase Storage (S3-compatible)**
- Required by the brief. R2's zero egress fees matter for a photo-heavy app the moment it's viewed a lot (every wardrobe grid load re-fetches thumbnails); Supabase Storage is the pragmatic default if already using Supabase for DB/Auth, with R2 as the cost-driven upgrade path — both are behind the same `StorageClient` interface.

**Auth: Supabase Auth (or Clerk)**
- Required by the brief. Both handle OAuth (Google/Apple — relevant since this is a personal, photo-heavy app where frictionless sign-in matters), session/JWT issuance, and are a fraction of the effort of hand-rolling auth. Supabase Auth is the default recommendation purely to consolidate vendors with the DB/Storage choice above; Clerk is the alternative if its more polished pre-built UI components are worth a second vendor.

**Queue: Redis + RQ (or Celery)**
- Simple, well-understood, sufficient at this scale; RQ specifically is lighter-weight than Celery for a small job surface (a handful of job types) and easier to reason about — Celery becomes worth its extra complexity only if job routing/retry needs grow significantly.

**Weather: OpenWeatherMap API** — required by the brief's "Weather" recommendation input; simple REST API, generous free tier at this usage scale, cached in `weather_cache` to bound cost.

**Calendar: Google Calendar API (read-only)** — covers the primary calendar provider for the target user; read-only scope minimizes the privacy/security surface for a feature that only needs event titles/times, not write access.

**Push: Web Push (VAPID) via the PWA service worker**, with transactional email (e.g., Resend) as a fallback for the Daily Outfit Notification when push isn't subscribed (e.g., first days after install, or on platforms with weaker web-push support).

## Hosting & Ops

| Layer | Choice | Why |
|---|---|---|
| Frontend | Vercel | Native Next.js support, edge CDN, image optimization, PR preview deploys |
| API + Workers | Fly.io or Railway | Container-based, cheap, simple Postgres/Redis add-ons, easy to graduate to AWS ECS Fargate later without a rewrite (both are just Docker containers) |
| Database | Supabase (managed Postgres + pgvector) | See above |
| Monitoring | Sentry (errors) + PostHog (product analytics) | Sentry across frontend+backend for one error pipeline; PostHog specifically to track the funnel from upload → tagged → worn, which is the product's core value-delivery loop |

## What's deliberately *not* chosen (and why)

- **Custom-trained fashion CNN** instead of a vision-LLM: not justified without a large labeled dataset; revisit only if per-image AI cost becomes a real constraint at scale.
- **Dedicated vector DB (Pinecone/Weaviate) at launch:** unnecessary operational surface at personal-wardrobe scale; `pgvector` is sufficient and the abstraction preserves the option.
- **Kubernetes / full microservices at launch:** overkill for the actual team size and traffic; the modular monolith + worker split already captures the scaling seam that matters first.
- **Native mobile app at launch:** the PWA covers the mobile-first requirement without doubling the codebase; native is a V3 decision made with real usage data, not upfront.
