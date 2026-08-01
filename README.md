# everydayjustyou

**Muse** — an AI-powered digital wardrobe assistant. Photograph your closet once; let AI catalog it, generate outfits, and style you daily.

Inspired by the closet computer from *Clueless*, rebuilt with modern multimodal AI (vision-based clothing detection, background removal, semantic search, and a conversational AI stylist).

Architecture and planning are in [`docs/README.md`](./docs/README.md) — full PRD, database schema, API architecture, folder structure, user flows, UI wireframes, AI architecture, implementation roadmap, sprint planning, and tech stack justification. Built to a **hard $0 budget** and designed as an **invite-only multi-user** product from day one (see PRD §1a).

## Status

**Phase 0 (Foundations)** is implemented — auth, RLS-enforced data isolation, invite-only signup, the T&C/consent gate, and an empty-state app shell. Phases 1+ (AI ingestion, outfit generation, Stylist chat, etc.) are speced in the docs but not yet built — see [`docs/roadmap/roadmap-and-sprints.md`](./docs/roadmap/roadmap-and-sprints.md).

## Running it locally

**Backend** (`services/api`):
```
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # fill in Supabase project details
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (`apps/web`):
```
cd apps/web
pnpm install
cp .env.local.example .env.local   # fill in Supabase project details
pnpm dev
```

**Database**: either `supabase start` (Supabase CLI — recommended, gives you real `auth`/`storage` and RLS you can actually test) or `docker compose -f infra/docker-compose.yml up -d` (DB-only, lighter, RLS is present but not meaningfully enforced locally — see `services/api/app/db/session.py` for why).