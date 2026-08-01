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
│   │   │   ├── ai/                   # AIClient, prompt templates, tool definitions
│   │   │   ├── integrations/         # WeatherClient, CalendarClient, StorageClient, PushClient
│   │   │   ├── core/                 # config, security/auth deps, logging, exceptions
│   │   │   └── db/                   # session, migrations entrypoint
│   │   ├── alembic/                  # DB migrations
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── ai-worker/                    # Async worker service (Redis/RQ or Celery consumer)
│       ├── worker/
│       │   ├── jobs/
│       │   │   ├── remove_background.py
│       │   │   ├── extract_attributes.py
│       │   │   ├── generate_embeddings.py
│       │   │   ├── render_outfit_collage.py
│       │   │   ├── generate_try_on.py        # V3
│       │   │   └── send_daily_notifications.py
│       │   ├── models/                        # local ML models (rembg, CLIP) or client wrappers
│       │   └── scheduler.py                    # cron-triggered jobs
│       ├── tests/
│       └── pyproject.toml
│
├── packages/
│   ├── ui/                           # shared design-system components (if/when a native app is added)
│   ├── types/                        # shared TS types, generated from FastAPI's OpenAPI schema
│   └── config/                       # shared eslint/tsconfig/tailwind/prettier config
│
├── infra/
│   ├── docker-compose.yml            # local dev: postgres+pgvector, redis, minio (S3-compatible)
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   └── worker.Dockerfile
│   └── terraform/                    # (post-MVP) IaC for prod infra if migrating off PaaS
│
├── docs/                             # this documentation set
├── .github/
│   └── workflows/                    # CI: lint, typecheck, test, build, preview deploy
├── package.json                      # workspace root
├── pnpm-workspace.yaml
└── README.md
```

## Notes

- **`services/api` vs `services/ai-worker`** are two independently deployable processes sharing the same Python package structure conventions but *not* the same runtime — the worker is CPU/GPU-bound and scales on queue depth, the API is I/O-bound and scales on request concurrency. They can still share a `services/api/app/services` import if useful (worker jobs call the same service-layer functions the API uses), achieved by packaging `app` as an installable local package rather than duplicating logic.
- **`packages/types`** is generated (not hand-written) from the FastAPI OpenAPI spec on each API change (`openapi-typescript`), so the frontend never drifts from the backend contract.
- **No `apps/mobile` in V1** — the PWA is mobile-first and installable; a React Native/Expo app is a V3+ addition and would land under `apps/mobile`, reusing `packages/types` and `packages/ui` tokens.
