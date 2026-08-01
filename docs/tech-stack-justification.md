# Tech Stack Justification

## $0 budget — hard constraint

This is a personal project (the developer + girlfriend + sister + a few family members, invite-only, not a public product), and every choice below is scoped to a **hard $0 budget**, not "cheap." Every service picked is a genuine free tier with no credit card requirement that turns into a bill on its own, not a paid tier that happens to be inexpensive at this usage level. Where a feature would naturally want a paid service, the alternative below is the free-tier-compatible substitute, called out explicitly rather than quietly assumed. This is the **locked-in stack** — decided after working through the tradeoffs, not re-derived per feature:

| Layer | Locked choice |
|---|---|
| Frontend | Next.js, shipped as a PWA (installable via Add to Home Screen — iPhone/iPad, no App Store/Apple Developer account/Mac needed). Dev machine: Windows. |
| Backend | FastAPI on Render or Railway free tier (cold starts accepted as a known tradeoff) |
| Database + Storage + Auth | Supabase free tier (Postgres + `pgvector` + Storage + Auth, one vendor) |
| Background removal | `rembg`, self-hosted, no per-image cost |
| AI vision + chat | Gemini API free tier (not OpenAI — no free tier there) |

## Frontend

**Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui-style primitives + Framer Motion**
- Next.js gives SSR/streaming for fast first paint (important for a "premium/fast" feel), file-based routing that maps cleanly to the screen list, and — via **Vercel's free tier** — edge CDN + image optimization at $0, which matters a lot for a photo-heavy app.
- Tailwind + a small owned component layer (rather than a heavy component library) keeps the Apple-like restraint achievable — utility CSS makes a strict spacing/type scale easy to enforce project-wide.
- Framer Motion for the small set of purposeful transitions (card → detail, swipe stack) called for in the design principles — used sparingly, not as a default.
- **PWA, not native app.** Installable on iPhone/iPad via Add to Home Screen, push-capable (Web Push/VAPID), camera-capable via `<input capture>`/`getUserMedia`, one codebase, no App Store review, no Apple Developer Program fee ($99/yr — directly ruled out by the $0 constraint), no Mac required for the Windows dev machine to build/ship with. A React Native app is deferred indefinitely — it would need a paid Apple Developer account to ship to real devices beyond Expo Go, which breaks the budget constraint outright.

## Backend

**FastAPI (Python, async), single deployable service**
- Async-native (matters for I/O-bound work: DB, storage, external AI calls), Pydantic gives typed request/response validation "for free," and auto-generated OpenAPI spec feeds the frontend's generated TypeScript client — contract drift between frontend/backend becomes a build-time problem, not a runtime one.
- Python is also the natural home for the AI/vision workloads (Gemini calls, `rembg`, CLIP), so there's one language and one deployable, not an API service plus a separate always-on worker service — see "Background jobs" below for why that's a budget decision, not just simplicity.
- **Hosted on Render or Railway free tier.** Both offer a genuine no-card free tier for a containerized Python service. The known tradeoff, accepted deliberately: the service spins down after a period of inactivity and cold-starts (several-second delay) on the next request. For a handful of family users opening the app a few times a day, this is a UX cost worth paying to stay at $0 — not a bug to engineer around.

## Database, Storage, Auth

**Supabase free tier — locked in, not one option among several**
- Bundles Postgres + `pgvector` + Storage + Auth under one vendor at $0, which is what makes the rest of the stack affordable: no separate vector DB bill, no separate storage bill, no separate auth bill.
- `pgvector` lets the *same* database serve as the vector store for embeddings at this scale (a wardrobe is hundreds to low-thousands of items per user, across a handful of users — nowhere near where a dedicated vector DB like Pinecone/Weaviate earns its (paid) operational cost).
- Supabase Auth handles invite-only account creation (the developer creates/approves each account — no public signup route), OAuth, and JWT issuance, and its Postgres integration is what makes real row-level security (not just app-level `user_id` filtering) practical — see [database-schema.md §RLS](./architecture/database-schema.md) for the enforcement pattern. This is the non-negotiable multi-user isolation requirement, and Supabase is what makes it nearly free to build in from day one instead of retrofitting later.
- Supabase Storage (not a separate S3/R2 bucket) holds all images — one vendor, one free-tier quota to track, and storage access is locked to authenticated per-user paths via Storage RLS policies (explicit setup step, documented in database-schema.md — default bucket settings are not trusted as-is).
- Trade-off: vendor lock-in to Supabase. Mitigated by keeping storage/auth behind thin client interfaces (`StorageClient`, auth dependency) so a future migration is a swap, not a rewrite, if this ever needs to leave the free tier.

## AI / Vision

**Gemini API free tier for chat reasoning, structured attribute extraction, and outfit rationale generation**
- OpenAI has no free tier, which rules out GPT-4o outright under the $0 constraint. Gemini's free tier (Google AI Studio / Gemini API) covers both vision (multimodal image understanding for attribute extraction) and text/tool-calling chat in one provider, at no cost for the request volumes a single-household-scale user base generates.
- Gemini's multimodal input handles the clothing-attribute-extraction task in the same call as the text reasoning, avoiding a separate custom-trained image classifier — which would need labeled fashion training data unavailable at this scale. Function/tool calling is what makes the Stylist chat reliably resolve "I have a job interview" into a real `generate_outfit(...)` call rather than free-text guessing.
- **Design for free-tier rate limits explicitly**, not as an afterthought: free-tier Gemini has per-minute and per-day request caps. With a handful of users, mitigations are: use the cheapest/fastest Gemini model tier (e.g. the Flash-class model) for bulk background tagging, reserve any heavier reasoning for interactive chat, cache aggressively (identical outfit-generation requests reuse the day's result, attribute extraction runs once per image and is persisted, never recomputed), and queue/rate-limit outbound calls in the `AIClient` so a burst (e.g. batch-uploading 40 items during onboarding) degrades to "processing may take a few minutes" rather than hitting a hard quota error.
- **Provider abstraction (`AIClient`)** stays a deliberate architectural choice — it isolates the app from Gemini's specific API shape and rate-limit behavior, and leaves room to add a second free-tier provider later (e.g. splitting bulk tagging and chat across two providers' free quotas) without touching calling code.
- **Third-party data-use disclosure (verified, not assumed):** per Google's own [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms), on the *free/unpaid* tier Google may use submitted content (including images) and generated responses to improve its products and ML models, and human reviewers may read/annotate input-output pairs (disconnected from the account/API key first). Google's own terms explicitly say: "do not submit sensitive, confidential, or personal information to the Unpaid Services." This is why the product's consent/T&C flow (PRD §7) discloses this plainly and why sensitive-category items are never sent to Gemini at all — that policy isn't precautionary, it's aligned with Google's own guidance for the free tier. (EEA/UK/Switzerland users get the stricter paid-tier data terms even on free usage, per the same terms page.)

**Background removal: `rembg` (U2Net/ISNet), self-hosted in the FastAPI process/background job**
- Open-source, no per-image API cost, runs fine on CPU (Render/Railway free tier is CPU-only, which `rembg` tolerates — slower than GPU but adequate at this volume), and this exact task (clean product-style background removal) is well within its accuracy envelope — no need for a paid API (e.g. remove.bg) at personal-wardrobe volume. Abstracted behind a `BackgroundRemover` interface so swapping implementations later is a one-file change.

**Embeddings: CLIP (image), self-hosted — Gemini embeddings API (text description)**
- CLIP (open-source, self-hosted via `open_clip`/`sentence-transformers`, same process as `rembg`) gives visual similarity (duplicate detection, "items that look like this") at no per-call cost — a hosted embedding endpoint was deliberately ruled out here since it would be a second AI bill.
- Text embeddings over the AI-generated description use the **Gemini embeddings API** (also free-tier) rather than OpenAI's `text-embedding-3-small`, consistent with the single-AI-vendor, $0 constraint.

## Background Jobs (no Redis)

**Postgres-backed job table + in-process async worker loop — not Redis/Celery/RQ**
- A separate always-on worker service plus a managed Redis instance is the standard pattern for this kind of pipeline, but neither Render nor Railway includes a durable free Redis tier, and running a second always-on service doubles the free-tier footprint for no budget-compatible gain. So the queue is a plain `processing_jobs` table in the already-free Supabase Postgres, and the "worker" is an `asyncio` background task started in-process by the same FastAPI service, polling that table.
- **Trade-off, accepted explicitly:** jobs only advance while the process is awake. Combined with Render/Railway's free-tier cold-start behavior, a job enqueued right as the service spins down could sit until the next request wakes it back up. At single-household usage (the next request is usually the user reopening the app moments later) this is an acceptable UX cost, not a correctness problem — nothing is lost, processing just resumes.
- **Scheduled jobs** (daily outfit notification, seasonal-rotation nudges) can't rely on an always-warm process either. Instead, a **GitHub Actions scheduled workflow** (`schedule: cron`, already free for this repo's CI) pings an internal `/internal/cron/*` endpoint at the configured times — this both wakes a sleeping free-tier instance and triggers the job, with zero additional infrastructure or cost.
- If usage ever outgrows this (many more users, heavier job volume), the exit ramp is well-defined: swap the polling loop for a real queue behind the same job-table interface — an infra change, not an application rewrite.

## Other Integrations

**Weather: OpenWeatherMap API** — generous free tier at this usage scale, cached in `weather_cache` to bound call volume further.

**Calendar: Google Calendar API (read-only)** — no cost, covers the primary calendar provider for the target users; read-only scope minimizes the privacy/security surface for a feature that only needs event titles/times.

**Push: Web Push (VAPID) via the PWA service worker**, free at any volume relevant here, with transactional email (Resend's free tier — 3,000 emails/month) as a fallback for the Daily Outfit Notification when push isn't subscribed.

**Monitoring: Sentry (errors) + PostHog (product analytics)** — both free tiers, generously sized for a handful of users; watch Sentry's free event quota if error volume ever spikes, since that's the one most likely to be brushed against first.

## Hosting & Ops

| Layer | Choice | Why |
|---|---|---|
| Frontend | Vercel free tier | Native Next.js support, edge CDN, image optimization, PR preview deploys — $0 at this traffic |
| Backend (API + in-process jobs) | Render or Railway free tier | Single deployable, container-based, $0; cold starts accepted |
| Database + Storage + Auth | Supabase free tier | See above |
| Scheduled jobs | GitHub Actions `schedule:` workflow | Free, already in the stack for CI, doubles as a wake-up ping |
| Monitoring | Sentry + PostHog free tiers | One error pipeline, one funnel-analytics tool, $0 |

## What's deliberately *not* chosen (and why)

- **OpenAI (any model):** no free tier — directly excluded by the $0 constraint, not a quality judgment.
- **Redis + Celery/RQ, or any managed queue:** no durable free tier on Render/Railway; a Postgres-backed job table covers the same need at this volume without a second paid-adjacent service.
- **Custom-trained fashion CNN** instead of a vision-LLM: not justified without a large labeled dataset, and would still need a hosting bill of its own.
- **Dedicated vector DB (Pinecone/Weaviate) at launch:** unnecessary operational surface (and cost) at this scale; `pgvector` inside the already-free Supabase Postgres is sufficient, and the `EmbeddingStore` abstraction preserves the option to move later.
- **Cloudflare R2 / S3 as primary storage:** would be a second vendor and a second thing to keep inside a free tier; Supabase Storage is already bundled at $0. R2 stays a documented scale-out option only, not something to set up now.
- **Kubernetes / full microservices, or a separate always-on worker service:** overkill for the actual usage, and a second always-on service doesn't fit a $0, free-tier-only budget anyway.
- **Native mobile app:** the PWA covers iPhone/iPad without an Apple Developer account ($99/yr, directly excluded) or a Mac; native is not revisited unless the budget constraint itself changes.
