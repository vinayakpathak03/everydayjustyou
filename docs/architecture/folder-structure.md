# Folder Structure

Monorepo (npm/pnpm workspaces for JS, uv/poetry for Python), managed with a single root so shared types and design tokens stay in sync across the web app and API.

```
muse/
├── apps/
│   └── web/                          # Next.js 14 (App Router), TypeScript
│       ├── app/
│       │   ├── (auth)/
│       │   │   ├── sign-in/
│       │   │   └── onboarding/
│       │   ├── (main)/
│       │   │   ├── today/            # Home — daily outfit / quick actions
│       │   │   ├── wardrobe/
│       │   │   │   ├── page.tsx      # grid + filters
│       │   │   │   ├── [id]/         # item detail
│       │   │   │   └── add/          # camera/upload + AI review flow
│       │   │   ├── outfits/
│       │   │   │   ├── generate/
│       │   │   │   └── [id]/
│       │   │   ├── stylist/          # AI chat
│       │   │   ├── analytics/
│       │   │   ├── packing/
│       │   │   ├── shopping/
│       │   │   ├── inspiration/
│       │   │   └── settings/
│       │   ├── api/                  # BFF route handlers (webhooks, SSE proxy)
│       │   └── layout.tsx
│       ├── components/
│       │   ├── ui/                   # design-system primitives (button, card, sheet...)
│       │   ├── garment/              # GarmentCard, GarmentGrid, AttributeEditor
│       │   ├── outfit/               # OutfitCard, ScoreBadge, OutfitCollage
│       │   ├── stylist/              # ChatBubble, ChatInput, OutfitCardInChat
│       │   └── analytics/            # charts, capsule suggestions
│       ├── hooks/                    # useGarments, useOutfitGenerator, useChatStream
│       ├── lib/
│       │   ├── api-client/           # typed client generated from OpenAPI schema
│       │   ├── auth/
│       │   └── utils/
│       ├── styles/                   # tailwind config, design tokens
│       ├── public/
│       └── service-worker.ts         # PWA offline cache + push
│
├── services/
│   ├── api/                          # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/              # thin HTTP layer (see api-architecture.md)
│   │   │   │   ├── garments.py
│   │   │   │   ├── outfits.py
│   │   │   │   ├── stylist.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── packing.py
│   │   │   │   ├── shopping.py
│   │   │   │   └── ...
│   │   │   ├── services/             # domain/business logic
│   │   │   │   ├── garment_service.py
│   │   │   │   ├── outfit_service.py
│   │   │   │   ├── stylist_service.py
│   │   │   │   ├── analytics_service.py
│   │   │   │   └── ...
│   │   │   ├── repositories/         # SQLAlchemy/SQLModel data access
│   │   │   ├── models/               # ORM models
│   │   │   ├── schemas/              # Pydantic request/response models
│   │   │   ├── ai/                   # AIClient (Gemini), prompt templates, tool definitions
│   │   │   ├── integrations/         # WeatherClient, CalendarClient, StorageClient, PushClient
│   │   │   ├── workers/              # job handlers, run in-process (no separate worker service — $0 budget, see system-architecture.md §3)
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── remove_background.py      # rembg, self-hosted
│   │   │   │   │   ├── extract_attributes.py      # Gemini vision call
│   │   │   │   │   ├── generate_embeddings.py     # CLIP (self-hosted) + Gemini text embeddings
│   │   │   │   │   ├── render_outfit_collage.py
│   │   │   │   │   └── generate_try_on.py         # V3
│   │   │   │   ├── models/                        # local ML models (rembg, CLIP weights)
│   │   │   │   └── poller.py                       # asyncio loop polling processing_jobs, started at app startup
│   │   │   ├── core/                 # config, security/auth deps, logging, exceptions
│   │   │   └── db/                   # session, migrations entrypoint
│   │   ├── alembic/                  # DB migrations
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── (no separate worker service — see system-architecture.md §3 for why: a second
│        always-on process doesn't fit a $0/free-tier-only hosting plan; internal/cron
│        endpoints in routers/ are what the GitHub Actions schedule: workflow pings for
│        daily notifications/seasonal-rotation, see api-architecture.md)
│
├── packages/
│   ├── ui/                           # shared design-system components (if/when a native app is added)
│   ├── types/                        # shared TS types, generated from FastAPI's OpenAPI schema
│   └── config/                       # shared eslint/tsconfig/tailwind/prettier config
│
├── infra/
│   ├── docker-compose.yml            # local dev: postgres+pgvector, minio (S3-compatible) — no redis
│   ├── docker/
│   │   └── api.Dockerfile            # single image, API + in-process job poller
│   └── terraform/                    # (post-MVP) IaC only if migrating off free-tier PaaS
│
├── docs/                             # this documentation set
├── .github/
│   └── workflows/                    # CI: lint, typecheck, test, build, preview deploy
├── package.json                      # workspace root
├── pnpm-workspace.yaml
└── README.md
```

## Notes

- **`services/api/app/workers`** runs in-process, not as a separate deployable — the job handlers call the exact same `services/` functions the HTTP routers use (e.g. `GarmentService.apply_extracted_attributes(...)`), so there's no logic duplication between the request path and the background-job path, and only one process to keep inside the free-tier hosting budget. If job volume ever outgrows this, the exit ramp is to promote `workers/` into its own deployable behind the same `processing_jobs` table interface — an infra change, not a rewrite.
- **`packages/types`** is generated (not hand-written) from the FastAPI OpenAPI spec on each API change (`openapi-typescript`), so the frontend never drifts from the backend contract.
- **No `apps/mobile` in V1** — the PWA is mobile-first and installable; a React Native/Expo app is a V3+ addition and would land under `apps/mobile`, reusing `packages/types` and `packages/ui` tokens.
