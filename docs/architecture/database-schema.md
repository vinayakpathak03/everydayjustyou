# Database Schema

PostgreSQL 15+ (Supabase free tier), with the `pgvector` and `pgcrypto` (for `gen_random_uuid()`) extensions enabled. All primary keys are UUIDs. All tables carry `created_at`/`updated_at` timestamps (`timestamptz`) unless noted.

**This is a multi-user, invite-only product** (developer + a handful of family members, not a single household) with hard per-user data isolation — every user-scoped table below carries `user_id` and has Row-Level Security enabled; see §9 for the enforcement pattern. This is non-negotiable and built in from the first migration, not retrofitted.

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ GARMENTS : owns
    USERS ||--o{ OUTFITS : creates
    USERS ||--o{ WEAR_LOGS : logs
    USERS ||--o{ CHAT_CONVERSATIONS : has
    USERS ||--|| STYLE_PROFILES : has
    USERS ||--o{ PACKING_LISTS : plans
    USERS ||--o{ SHOPPING_RECOMMENDATIONS : receives

    GARMENTS ||--o{ GARMENT_IMAGES : has
    GARMENTS ||--o{ GARMENT_TAGS : tagged_with
    GARMENTS ||--o{ GARMENT_EMBEDDINGS : embedded_as
    GARMENTS ||--o{ OUTFIT_ITEMS : appears_in
    GARMENTS ||--o{ WEAR_LOGS : worn_as
    GARMENTS ||--o{ PACKING_LIST_ITEMS : packed_as
    GARMENTS }o--|| BRANDS : made_by

    TAGS ||--o{ GARMENT_TAGS : applied_via

    OUTFITS ||--o{ OUTFIT_ITEMS : contains
    OUTFITS ||--o{ OUTFIT_FEEDBACK : rated_by
    OUTFITS ||--o{ WEAR_LOGS : worn_as

    CHAT_CONVERSATIONS ||--o{ CHAT_MESSAGES : contains

    PACKING_LISTS ||--o{ PACKING_LIST_ITEMS : contains

    USERS ||--o{ MOODBOARDS : curates
    MOODBOARDS ||--o{ MOODBOARD_ITEMS : contains
    MOODBOARD_ITEMS ||--o{ INSPIRATION_MATCHES : matched_to
    GARMENTS ||--o{ INSPIRATION_MATCHES : matches

    USERS ||--o{ OUTFIT_PLANS : schedules
    OUTFIT_PLANS }o--|| OUTFITS : plans

    USERS ||--o{ INVITES : issues
    USERS ||--o{ PROCESSING_JOBS : owns
```

## 2. Core Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| email | text unique | |
| display_name | text | |
| avatar_url | text | for virtual try-on reference photo, optional |
| auth_provider_id | text | external auth provider subject id (Supabase/Clerk) |
| timezone | text | default `UTC`, used for daily notification scheduling |
| notification_time | time | user's preferred daily-outfit push time |
| location | jsonb | `{lat, lng, city}` cached for weather lookups |
| onboarding_completed_at | timestamptz nullable | |
| consent_dev_photo_access | boolean not null default `true` | developer may receive a copy of uploaded photos for debugging; pre-checked at signup, toggle lives on the same screen as the T&C (not routed around it), revocable any time in Settings |
| tc_version | text nullable | version/hash of the T&C text the user accepted, so a future rewrite can detect who's on stale consent |
| tc_accepted_at | timestamptz nullable | required before `onboarding_completed_at` can be set |
| invited_by | uuid nullable, FK → users | who invited this account, for the invite-only signup trail |
| created_at / updated_at | timestamptz | |

### `invites`
Backs invite-only signup — there is no public registration route. The developer creates a row here (or directly provisions the Supabase Auth user) per person they're inviting.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| email | text | the invited person's email |
| invited_by | uuid FK → users | |
| token | text unique | included in the signup link sent out-of-band (e.g. a text message) |
| status | text | `pending, accepted, revoked` |
| accepted_by | uuid nullable, FK → users | set once the invite is redeemed |
| expires_at | timestamptz nullable | |
| created_at | timestamptz | |

### `style_profiles`
One-to-one with `users`. Recomputed periodically from analytics + explicit prefs, injected into AI Stylist system context.
| Column | Type | Notes |
|---|---|---|
| user_id | uuid PK, FK → users | |
| preferred_colors | text[] | |
| preferred_aesthetics | text[] | e.g. `{quiet_luxury, minimalist}` |
| sizes | jsonb | `{tops: "M", bottoms: "8", shoes: "8.5"}` |
| dislikes | text[] | free-text notes AI should avoid |
| summary | text | LLM-generated rolling summary used as chat context |
| updated_at | timestamptz | |

### `brands`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| name | text unique | |
| tier | text nullable | e.g. `luxury`, `contemporary`, `fast_fashion` — used for shopping/analytics |

### `garments`
The core catalog item.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | |
| brand_id | uuid FK → brands, nullable | |
| category | text | enum: `top, bottom, dress, outerwear, shoes, bag, accessory, jewelry` |
| subcategory | text nullable | e.g. `blouse`, `wide-leg trouser` |
| primary_color | text | |
| secondary_colors | text[] | |
| pattern | text nullable | `solid, striped, floral, plaid, animal_print, other` |
| fabric_guess | text nullable | AI best-guess, always user-editable |
| fabric_confidence | text nullable | `low, medium, high` |
| sleeve_length | text nullable | `sleeveless, short, three_quarter, long, n/a` |
| neckline | text nullable | |
| fit | text nullable | `fitted, relaxed, oversized` |
| season | text[] | `{spring, summer, fall, winter}` |
| occasion | text[] | `{casual, work, formal, evening, athletic, loungewear}` |
| formality_score | smallint | 1–10 |
| size | text nullable | |
| color_hex | text nullable | dominant color as hex, for swatch UI + color filtering |
| purchase_price | numeric(10,2) nullable | for cost-per-wear |
| purchase_date | date nullable | |
| purchase_source | text nullable | store/site name |
| condition | text nullable | `new, like_new, good, worn` |
| acquisition_type | text nullable | `new, pre_loved, rental, handmade, gifted, undefined` — powers the Wardrobe Composition chart (PRD §6.15) |
| is_favorite | boolean default false | |
| is_archived | boolean default false | soft-hide from active wardrobe without deleting |
| ai_description | text nullable | generated natural-language description (embedding source); null for manual entries |
| ai_confidence | jsonb nullable | per-attribute confidence scores from the vision worker; null for manual entries |
| status | text | `processing, needs_review, ready` |
| entry_mode | text not null default `ai_photo` | `ai_photo` (goes through §5.1's rembg+Gemini pipeline) or `manual` (sensitive-category path — never sent to any AI provider) |
| sensitive_category | boolean not null default `false` | auto-set true for underwear/lingerie/similar categories, user-togglable either direction. When true: `entry_mode` must be `manual`, no image is ever sent to Gemini, and any stored photo is excluded from outfit-generation candidate retrieval, shared/social views, and the dev-photo-access pipeline **regardless of `users.consent_dev_photo_access`** — this exclusion overrides that consent setting, not the reverse |
| manual_description | text nullable | free-text description, required when `entry_mode = manual` (e.g. "5 pairs black cotton briefs") |
| manual_quantity | int nullable | for manual entries logged as a count rather than individual items |
| created_at / updated_at | timestamptz | |

Indexes: `(user_id, category)`, `(user_id, is_archived)`, GIN on `season`, `occasion`, `secondary_colors`.

Application-level check: a row with `sensitive_category = true` must have `entry_mode = 'manual'` — enforced in the service layer (and ideally a Postgres `CHECK` constraint) so a sensitive item can never accidentally enter the AI pipeline via a code path that skips the app-level guard.

### `garment_images`
Multiple photos per item.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| garment_id | uuid FK → garments | |
| kind | text | `raw, processed, detail, worn_on_body` |
| storage_url | text | object storage key/URL (processed, transparent PNG for `processed`) |
| width / height | int | |
| sort_order | smallint | |
| status | text | `processing, bg_removed, tagged, failed` |
| is_primary | boolean default false | used as the card thumbnail |
| created_at | timestamptz | |

### `garment_embeddings`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| garment_id | uuid FK → garments | |
| kind | text | `image_clip, text_description` |
| embedding | vector(512) or vector(1536) | dimension depends on model; separate columns or separate rows by `kind` |
| model | text | model name/version used, for future re-embedding migrations |
| created_at | timestamptz | |

Index: `hnsw (embedding vector_cosine_ops)`.

### `processing_jobs`
The background job queue — a plain Postgres table polled by an in-process `asyncio` worker loop in the FastAPI service, replacing Redis/Celery/RQ (see [system-architecture.md §5.6](../architecture/system-architecture.md), driven by the $0 hosting budget: no durable free Redis tier on Render/Railway, and a second always-on worker service doesn't fit a free-tier-only plan).
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | |
| type | text | `process_image, generate_embedding, daily_notification, ...` |
| payload | jsonb | job-specific input, e.g. `{garment_image_id}` |
| status | text | `pending, running, done, failed` |
| attempts | smallint default 0 | for basic retry-with-backoff on transient failures (e.g. a Gemini rate-limit response) |
| error | text nullable | last failure reason, if any |
| created_at / updated_at | timestamptz | |

Indexed on `(status, created_at)` for efficient polling (`WHERE status = 'pending' ORDER BY created_at LIMIT N`). Rows are cheap to leave around after completion (no separate cleanup job needed at this volume) but a periodic delete of old `done` rows keeps the table small.

### `tags` / `garment_tags`
Freeform user tags (many-to-many), distinct from AI-structured attributes.
| `tags` | Type |
|---|---|
| id uuid PK | |
| user_id uuid FK | |
| name text | unique per user |

| `garment_tags` | Type |
|---|---|
| garment_id uuid FK | |
| tag_id uuid FK | |
| PK (garment_id, tag_id) | |

## 3. Outfits

### `outfits`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | |
| name | text nullable | user-editable label |
| source | text | `generated, manual, shuffle, chat` — `manual` = built on the Canvas (§6.13), `shuffle` = Dress Me/Quick Shuffle (§6.14) |
| context | jsonb | inputs used to generate it: `{weather, occasion, mood, event, aesthetic}` |
| score | smallint | 1–100 |
| score_breakdown | jsonb | `{color_harmony, formality_fit, weather_fit, novelty}` |
| rationale | text | LLM-generated "why this works" |
| collage_image_url | text nullable | rendered flat-lay preview |
| canvas_layout | jsonb nullable | populated only for `source = manual` — per-item `{garment_id, x, y, scale, rotation, z_index}` so a Canvas outfit can be reopened and re-edited exactly as arranged |
| is_favorite | boolean default false | |
| created_at | timestamptz | |

### `outfit_items`
| Column | Type | Notes |
|---|---|---|
| outfit_id | uuid FK | |
| garment_id | uuid FK | |
| slot | text | `top, bottom, dress, outerwear, shoes, bag, accessory, jewelry` |
| PK (outfit_id, garment_id, slot) | | |

### `outfit_feedback`
Explicit user signal (swipe like/dislike, star rating) used to refine future scoring/novelty weighting.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| outfit_id | uuid FK | |
| user_id | uuid FK | |
| rating | text | `liked, disliked, worn, saved` |
| created_at | timestamptz | |

## 4. Wear Tracking & Analytics

### `wear_logs`
Backbone of Closet Analytics (most/least worn, cost-per-wear, "I wore this yesterday").
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| garment_id | uuid FK nullable | nullable so a whole `outfit_id` can be logged without enumerating items redundantly (a trigger/view expands to per-item wear counts) |
| outfit_id | uuid FK nullable | |
| worn_on | date | |
| notes | text nullable | |
| created_at | timestamptz | |

A materialized view `garment_wear_stats` (refreshed nightly or on-write) aggregates: `times_worn`, `last_worn_on`, `cost_per_wear = purchase_price / NULLIF(times_worn,0)`.

A second view, `wardrobe_usage_stats`, computes the rolling-window figures behind PRD §6.15's usage gauge and composition chart: `% of active garments with >=1 wear_logs row in the trailing N days` (default 90), plus the same figure for the *prior* N-day window so the UI can show a trend delta ("You wore 20% more"), and a `GROUP BY acquisition_type` breakdown for the composition donut. Computed as a view rather than stored, since it's cheap to derive from `wear_logs` + `garments` at read time and never needs to be point-in-time-accurate the way `garment_wear_stats`' cost-per-wear does.

## 5. Conversational AI

### `chat_conversations`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| title | text nullable | auto-summarized after first exchange |
| created_at / updated_at | timestamptz | |

### `chat_messages`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| conversation_id | uuid FK | |
| role | text | `user, assistant, tool` |
| content | text | |
| tool_calls | jsonb nullable | recorded function-calling trace for debugging |
| referenced_garment_ids | uuid[] nullable | for rendering rich cards + audit of grounding |
| referenced_outfit_id | uuid nullable | |
| created_at | timestamptz | |

## 6. Packing & Shopping

### `packing_lists`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| destination | text | |
| start_date / end_date | date | |
| trip_type | text | `business, leisure, beach, adventure, mixed` |
| weather_summary | jsonb nullable | cached forecast/seasonal-average used |
| created_at | timestamptz | |

### `packing_list_items`
| Column | Type | Notes |
|---|---|---|
| packing_list_id | uuid FK | |
| garment_id | uuid FK | |
| outfit_id | uuid FK nullable | groups items belonging to the same planned outfit |
| is_packed | boolean default false | checklist state |
| PK (packing_list_id, garment_id) | | |

### `shopping_recommendations`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| reason | text | `gap_fill, outfit_completion, duplicate_upgrade` |
| target_attributes | jsonb | archetype the recommendation is described by (category/color/etc.), not a specific SKU |
| related_outfit_id | uuid nullable | the outfit this would complete/improve |
| external_product_url | text nullable | populated once a retailer-search integration exists (V2+) |
| status | text | `suggested, dismissed, purchased` |
| created_at | timestamptz | |

## 6a. Moodboards & Weekly Planner

### `moodboards`
User-curated inspiration boards (PRD §6.11) — distinct from `garments` (owned items) and from AI-generated Fashion Inspiration presets (§6.10 in the PRD, no dedicated table — those are computed, not stored).
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | |
| name | text | e.g. `Party`, `Office`, `Summer`, `Bday wishes` |
| cover_image_url | text nullable | defaults to the most recent item's image |
| created_at / updated_at | timestamptz | |

### `moodboard_items`
The individual saved clips.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| moodboard_id | uuid FK → moodboards | |
| source_url | text nullable | original web/share-sheet URL, if any |
| storage_url | text | the saved image, in object storage |
| ai_description | text nullable | same vision-extraction pipeline as garments (§5.1), for search/matching |
| embedding | vector(512) nullable | image embedding, for matching against owned garments |
| sort_order | smallint | |
| created_at | timestamptz | |

### `inspiration_matches`
Precomputed "you already own something like this" links, refreshed when a new moodboard item is saved or a new garment is added.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| moodboard_item_id | uuid FK | |
| garment_id | uuid FK | |
| similarity | numeric(4,3) | cosine similarity between embeddings |
| created_at | timestamptz | |

### `outfit_plans`
Backbone of the Weekly Planner (PRD §6.12) — a *prospective* assignment of an outfit to a future date, as opposed to `wear_logs` which is a *retrospective* record of what was actually worn.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | |
| outfit_id | uuid FK → outfits | |
| planned_date | date | |
| status | text | `planned, worn, skipped` — transitions to `worn` writes a corresponding `wear_logs` row |
| source | text | `user, daily_notification` — who created the plan |
| created_at / updated_at | timestamptz | |

Unique `(user_id, planned_date)` if only one planned outfit per day is allowed for V1 (simplest); relax to a composite key with a `slot`/`time_of_day` column later if multiple outfits per day (e.g., day look + evening look) become a requirement. The Daily Outfit Notification (§5.6 in system-architecture.md) checks `outfit_plans` for the day before generating a fresh suggestion, so a user-planned outfit always takes precedence.

## 7. Notifications & Integrations

### `notifications`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| type | text | `daily_outfit, wear_reminder, seasonal_rotation` |
| payload | jsonb | |
| sent_at | timestamptz nullable | |
| read_at | timestamptz nullable | |
| created_at | timestamptz | |

### `calendar_connections`
| Column | Type | Notes |
|---|---|---|
| user_id | uuid PK, FK | |
| provider | text | `google` |
| access_token_encrypted | text | encrypted at rest |
| refresh_token_encrypted | text | |
| connected_at | timestamptz | |

### `weather_cache`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| location_key | text | geohash or `lat,lng` rounded |
| date | date | |
| forecast | jsonb | |
| fetched_at | timestamptz | |

Unique `(location_key, date)`, short TTL eviction.

## 8. Design Notes

- **Soft deletes** via `is_archived`/`status` fields rather than hard deletes on `garments`, so analytics/history stay intact; a separate hard-delete (GDPR-style data export/delete) is a distinct admin operation, not the everyday "remove from closet" action.
- **All AI-derived fields are user-overridable** — no attribute is read-only; corrections should ideally be captured (V2: a `garment_attribute_corrections` audit table) to enable future prompt/model tuning, but is not required for V1.
- **`user_id` scoping everywhere**, enforced at the database layer via Row-Level Security (§9), not just app-level filtering — this product is multi-user (invite-only) from day one, not a single household with multi-tenancy deferred.
- **jsonb over rigid columns** for evolving/optional structured data (`context`, `score_breakdown`, `ai_confidence`) keeps the schema stable while the AI layer iterates.
- **`moodboard_items` vs. `garments`** are deliberately separate tables even though both run through the same vision/embedding pipeline — a moodboard item is a *reference the user doesn't own*, and conflating it with owned inventory would corrupt every feature that assumes `garments` = "things in the closet" (Outfit Generator, Analytics, Shopping gap detection).

## 9. Row-Level Security (multi-user isolation — non-negotiable)

Every table above that carries `user_id` (`garments`, `outfits`, `wear_logs`, `chat_conversations`, `moodboards`, `packing_lists`, `shopping_recommendations`, `outfit_plans`, `notifications`, `style_profiles`, etc. — everything except lookup tables like `brands`/`tags`) has RLS **enabled**, with a policy of this shape:

```sql
alter table garments enable row level security;

create policy "garments_owner_select" on garments
  for select using (auth.uid() = user_id);

create policy "garments_owner_insert" on garments
  for insert with check (auth.uid() = user_id);

create policy "garments_owner_update" on garments
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "garments_owner_delete" on garments
  for delete using (auth.uid() = user_id);
```

(`auth.uid()` is Supabase's helper reading the `sub` claim off the current Postgres session's JWT-derived context — the same mechanism Supabase's own client libraries rely on.)

**Why this matters for how FastAPI connects to Postgres:** the easy-but-wrong integration pattern is for the backend to hold a single connection using Supabase's `service_role` key, which **bypasses RLS by design** (it's meant for trusted server-side admin operations) — if FastAPI used that key for ordinary user requests, every RLS policy above would be inert and isolation would fall back to whatever `WHERE user_id = ...` clauses the app happens to remember to write, which is exactly the "even by accident" failure mode this product must not have. Instead:

- Each authenticated request gets a Postgres session/transaction with the requesting user's id set as a local claim (`select set_config('request.jwt.claim.sub', :user_id, true)`, or equivalent via a connection-pooled role that maps the validated JWT), so `auth.uid()` resolves correctly and RLS applies exactly as it would through Supabase's own APIs.
- The `service_role` key is reserved for a short, explicit list of genuinely cross-user admin operations (e.g. the invite-acceptance flow that needs to look up an `invites` row before the invitee's own account/session exists) — never for routine per-user reads/writes.
- This is verified with a test that asserts a second user's authenticated session cannot read/write another user's rows even when the query has no `WHERE user_id` clause at all — the database, not the query, is the isolation boundary.

## 10. Storage Bucket Policies (explicit setup step, not a default)

Supabase Storage buckets are **not** left at default settings — this is called out explicitly because a misconfigured public bucket is one of the most common and most damaging mistakes at this stage:

- Every bucket (`garment-images`, `moodboard-images`, etc.) is created **private**, never "public."
- Objects are stored under a per-user path prefix (`{bucket}/{user_id}/{garment_id}/{filename}`), and Storage RLS policies on `storage.objects` restrict access to `auth.uid()::text = (storage.foldername(name))[1]` (i.e., the first path segment must match the requesting user) for select/insert/update/delete.
- Signed URLs (short-lived) are used for any client-side image display rather than making objects public — the frontend never constructs a raw public storage URL.
- Verifying bucket visibility and the per-user policy is a required Phase 0 setup step (see roadmap-and-sprints.md), checked manually against the Supabase dashboard before any real user photo is uploaded, not assumed from the bucket-creation defaults.
