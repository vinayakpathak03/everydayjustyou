# API Architecture

FastAPI, async, versioned under `/api/v1`. Auth via short-lived JWT (issued by Supabase Auth/Clerk) validated on every request via a dependency; refresh handled client-side by the auth provider's SDK.

## 1. Conventions

- **Base URL:** `/api/v1`
- **Auth:** `Authorization: Bearer <jwt>` on all endpoints except `/auth/*` webhooks.
- **Pagination:** cursor-based (`?cursor=...&limit=50`) for wardrobe/outfits lists — offset pagination degrades once wardrobes hit hundreds of items with frequent inserts.
- **Errors:** RFC 7807-style problem JSON: `{type, title, status, detail, instance}`.
- **Long-running work:** upload endpoints return `202 Accepted` immediately with a resource in `processing` status; client polls `GET` or subscribes via `GET /events` (SSE) for status transitions — never a blocking request during AI processing.
- **Idempotency:** mutating endpoints that trigger AI work accept an `Idempotency-Key` header to avoid duplicate processing on client retry.
- **Rate limiting:** per-user token bucket at the gateway (esp. on `/stylist/chat` and `/garments/images` given AI cost).

## 2. Router Map

```
/api/v1
├── /auth                 (session bootstrap, webhook from auth provider)
├── /users/me              GET, PATCH profile + preferences
├── /style-profile         GET, PATCH
├── /garments               CRUD + search/filter
│   └── /{id}/images         upload, list, delete, reorder
├── /outfits                CRUD, generate, favorite
│   └── /generate            POST — the Outfit Generator (6.2/6.3 in PRD)
│   └── /{id}/alternatives   POST — swap one slot, re-score
│   └── /{id}/feedback       POST — like/dislike/worn/saved
├── /wear-logs              POST log, GET history
├── /analytics              GET most-worn, least-worn, cost-per-wear,
│                               capsule-suggestions, missing-essentials,
│                               duplicates, seasonal-rotation
├── /stylist/chat           POST (streamed SSE) + conversation history
├── /packing-lists          CRUD + generate
├── /shopping               GET recommendations, POST dismiss/purchased
├── /try-on                 POST generate (V3)
├── /inspiration            GET aesthetic presets, POST generate-from-aesthetic
├── /notifications          GET, PATCH read, /settings
├── /integrations/calendar  connect, disconnect, status
├── /integrations/weather   (internal use, not user-facing directly)
└── /admin (internal)       health, model/version info, cost dashboards
```

## 3. Key Endpoints — Contracts

### `POST /garments/images`
Upload a raw photo, kicks off the ingestion pipeline (§5.1 of system-architecture.md).
```
Request: multipart/form-data { file, garment_id?: uuid (omit to create new garment) }
Response 202:
{
  "garment_id": "uuid",
  "image_id": "uuid",
  "status": "processing"
}
```

### `GET /garments/{id}` (poll during processing, or subscribe via SSE below)
```
{
  "id": "uuid",
  "status": "processing | needs_review | ready",
  "category": "top",
  "primary_color": "sage green",
  "ai_confidence": { "pattern": "high", "fabric_guess": "low" },
  "images": [ { "id": "...", "kind": "processed", "url": "...", "is_primary": true } ],
  ...
}
```

### `GET /garments/events` (SSE)
Server-sent events stream of status transitions for the current user's in-flight uploads — avoids client polling loops.

### `GET /garments?category=top&season=summer&color=pink&cursor=...`
Faceted browse/search; combines structured filters with optional `?q=` free text routed to the embedding-backed search.

### `POST /outfits/generate`
```
Request:
{
  "context": {
    "occasion": "job_interview" | "dinner" | null,
    "weather": { "auto": true } | { "override": {...} },
    "mood": "confident" | null,
    "aesthetic": "quiet_luxury" | null,
    "color_preference": "pink" | null,
    "exclude_recently_worn_days": 7,
    "count": 3
  }
}
Response 200:
{
  "outfits": [
    {
      "id": "uuid",
      "score": 87,
      "score_breakdown": { "color_harmony": 90, "occasion_fit": 85, "weather_fit": 88, "novelty": 70 },
      "rationale": "The sage trench and cream trousers...",
      "items": [ { "garment_id": "...", "slot": "outerwear", ... }, ... ],
      "collage_image_url": "..."
    }
  ]
}
```

### `POST /outfits/{id}/alternatives`
```
Request: { "swap_slot": "shoes" }
Response 200: { "outfit": { ...same shape, one slot changed, re-scored... } }
```

### `POST /stylist/chat` (SSE stream)
```
Request: { "conversation_id": "uuid" | null, "message": "I have a job interview" }
Streamed response: incremental text tokens + a final structured event:
event: outfit_cards
data: { "outfits": [ ... ] }
```
Internally implements the tool-calling loop from system-architecture.md §5.3 (`search_wardrobe`, `get_weather`, `get_calendar_events`, `generate_outfit`, `log_wear`, `get_wear_history`).

### `GET /analytics/summary`
```
{
  "most_worn": [ {garment_id, times_worn}, ... ],
  "least_worn": [ ... ],
  "cost_per_wear": [ {garment_id, cost_per_wear}, ... ],
  "capsule_suggestions": [ {garment_id, reason}, ... ],
  "missing_essentials": [ {archetype: "white button-down", reason} ],
  "duplicates": [ {garment_ids: [...], similarity: 0.94} ],
  "seasonal_rotation": [ {garment_id, last_worn_on, suggestion: "pack_away"} ]
}
```

### `POST /packing-lists/generate`
```
Request: { "destination": "Lisbon", "start_date": "...", "end_date": "...", "trip_type": "leisure" }
Response: { "packing_list": { id, items: [...], outfits: [...], weather_summary: {...} } }
```

### `GET /shopping/recommendations`
Returns gap-fill/completion suggestions per §6.7 of the PRD.

## 4. Internal Service Boundaries (within the FastAPI app)

```
routers/          → thin HTTP layer, request/response models only, no business logic
services/         → domain logic (OutfitService, GarmentService, StylistService, AnalyticsService...)
repositories/     → DB access (SQLAlchemy/SQLModel queries), one per aggregate
ai/               → AIClient abstraction (chat, vision, embeddings) + prompt templates
integrations/     → WeatherClient, CalendarClient, StorageClient, PushClient
workers/          → job definitions consumed by the queue (separate deployable, imports from services/)
```

Routers never talk to the database or AI providers directly — every call goes through a `service`, which is what makes `workers/` able to reuse the exact same `GarmentService.apply_extracted_attributes(...)` logic the API would use, avoiding logic duplication between the sync API and async workers.

## 5. Streaming & Real-Time

- **Chat:** SSE (`text/event-stream`) — simpler than WebSocket for a one-way token stream, works cleanly through Vercel/CDN, and the client only ever needs to *receive* streamed tokens, not send mid-stream.
- **Upload status:** SSE for the "your item is ready" transition, so the wardrobe grid updates live without polling.
- **Daily notifications:** not real-time — delivered via Web Push (VAPID) triggered by the scheduled worker, independent of any open session.

## 6. AuthN/AuthZ

- Authentication delegated to Supabase Auth (or Clerk) — handles email/password, OAuth (Google/Apple), and session/JWT issuance. FastAPI validates the JWT signature/claims on each request via a dependency (`get_current_user`).
- Authorization is simple row-level ownership (`resource.user_id == current_user.id`) enforced in the repository layer for V1 (single-user-owns-their-data model); the schema's `user_id` scoping makes a future household/shared-closet role model additive.
- Secrets (calendar OAuth tokens) encrypted at rest (e.g., via `pgcrypto` or an app-level envelope encryption key from a secrets manager).

## 7. External Integration Clients

| Client | Wraps | Notes |
|---|---|---|
| `AIClient` | OpenAI (primary), pluggable for Anthropic | chat completion w/ tools, vision extraction, embeddings — single retry/timeout/cost-logging wrapper |
| `StorageClient` | S3/R2/Supabase Storage | signed upload URLs, resize-on-read via CDN |
| `WeatherClient` | OpenWeatherMap | cached in `weather_cache` |
| `CalendarClient` | Google Calendar | read-only scope, token refresh handled here |
| `PushClient` | Web Push (VAPID) | falls back to email via a transactional email provider (e.g., Resend) if push isn't subscribed |
