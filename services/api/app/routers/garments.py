import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db as get_rls_scoped_db
from app.integrations.storage import get_storage_client
from app.models.garment import SENSITIVE_CATEGORIES, Garment, GarmentEmbedding, GarmentImage
from app.models.outfit import OutfitItem
from app.models.processing_job import ProcessingJob
from app.models.wear_log import WearLog
from app.schemas.garment import (
    GarmentImageUploadOut,
    GarmentManualCreate,
    GarmentOut,
    GarmentUpdate,
)

router = APIRouter(prefix="/garments", tags=["garments"])

# Garment has no `images` relationship/column — GarmentOut.images is populated by
# hand-assigning a plain instance attribute right before serialization (safe: it's
# not a mapped name, SQLAlchemy instances accept arbitrary attributes like any
# Python object). Deliberate: an async-safe `relationship()` needs an explicit
# eager-load per query anyway, so there's no simplicity lost — and it keeps each
# endpoint honest about whether it actually fetched images or not.

ACCEPTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


@router.post("/images", response_model=GarmentImageUploadOut, status_code=202)
async def upload_image(
    file: UploadFile,
    garment_id: UUID | None = None,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> GarmentImageUploadOut:
    """Kicks off the ingestion pipeline (system-architecture.md §5.1). Returns
    202 immediately — processing happens async via app/workers/poller.py, the
    client subscribes to /garments/events (SSE) or polls GET /garments/{id}."""
    if file.content_type not in ACCEPTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail={"type": "unsupported_media_type", "status": 415},
        )

    if garment_id is not None:
        garment = (
            await db.execute(select(Garment).where(Garment.id == garment_id))
        ).scalar_one_or_none()
        if garment is None:
            raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})
        if garment.sensitive_category:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "sensitive_no_ai_pipeline",
                    "title": "Sensitive-category items don't use the AI photo pipeline",
                    "status": 400,
                },
            )
    else:
        garment = Garment(user_id=current.id, category="unknown", status="processing")
        db.add(garment)
        await db.flush()

    raw_bytes = await file.read()
    raw_path = f"{current.id}/{garment.id}/raw-{file.filename}"
    storage = get_storage_client()
    await asyncio.to_thread(storage.upload, raw_path, raw_bytes, file.content_type)

    image = GarmentImage(
        garment_id=garment.id, kind="raw", storage_url=raw_path, status="processing"
    )
    db.add(image)
    await db.flush()

    db.add(
        ProcessingJob(
            user_id=current.id,
            type="process_image",
            payload={"garment_image_id": str(image.id)},
        )
    )
    await db.flush()

    return GarmentImageUploadOut(garment_id=garment.id, image_id=image.id, status="processing")


@router.post("/manual", response_model=GarmentOut, status_code=201)
async def create_manual_garment(
    body: GarmentManualCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> Garment:
    """Sensitive-category manual entry (PRD §7.1 item 4) — no processing_jobs row
    is ever created, so this item can never reach rembg or Gemini. Photo-optional
    entry is intentionally text/quantity-only in this version; an optional-photo
    variant that stores-without-processing is a fast follow, not yet built."""
    is_sensitive = body.sensitive_category or body.category.lower() in SENSITIVE_CATEGORIES
    garment = Garment(
        user_id=current.id,
        category=body.category,
        color_hex=body.color_hex,
        entry_mode="manual",
        sensitive_category=is_sensitive,
        manual_description=body.manual_description,
        manual_quantity=body.manual_quantity,
        status="ready",
    )
    db.add(garment)
    await db.flush()
    await db.refresh(garment)
    garment.images = []  # not loaded via relationship in this minimal pass
    return garment


@router.get("", response_model=list[GarmentOut])
async def list_garments(
    category: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=50, le=100),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> list[GarmentOut]:
    stmt = select(Garment).order_by(Garment.created_at.desc()).limit(limit)
    if category:
        stmt = stmt.where(Garment.category == category)
    if not include_archived:
        stmt = stmt.where(Garment.is_archived.is_(False))
    garments = list((await db.execute(stmt)).scalars())

    # One batched query for every garment's primary (or first) image, rather than
    # N+1 per-item queries — the grid view needs a thumbnail per card, so skipping
    # images here isn't actually an option the way it might be for other list views.
    garment_ids = [g.id for g in garments]
    images_by_garment: dict[UUID, list[GarmentImage]] = {gid: [] for gid in garment_ids}
    if garment_ids:
        all_images = list(
            (
                await db.execute(
                    select(GarmentImage)
                    .where(GarmentImage.garment_id.in_(garment_ids))
                    .order_by(GarmentImage.is_primary.desc(), GarmentImage.sort_order)
                )
            ).scalars()
        )
        for image in all_images:
            images_by_garment[image.garment_id].append(image)

    for g in garments:
        g.images = images_by_garment[g.id][:1]  # thumbnail only — full set is on the detail screen

    # The bucket is private (deliberately — see storage.py), so the raw
    # storage_url path isn't loadable by a browser; every image needs a
    # signed URL before it leaves the API. Built on Pydantic copies, not the
    # ORM rows themselves, so there's no risk of a signed URL ever getting
    # flushed back into the real storage_url column.
    storage_client = get_storage_client()
    paths = [img.storage_url for g in garments for img in g.images]
    signed = await asyncio.to_thread(storage_client.signed_urls, paths)
    results = [GarmentOut.model_validate(g) for g in garments]
    for result in results:
        for img in result.images:
            img.storage_url = signed.get(img.storage_url, img.storage_url)
    return results


@router.get("/events")
async def garment_events(
    current: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """SSE stream of status transitions for the current user's in-flight uploads —
    avoids client polling loops (docs/architecture/api-architecture.md §5). Simple
    poll-the-DB implementation, not a pub/sub system, consistent with the no-Redis
    constraint (system-architecture.md §5.6).

    Deliberately does NOT use the ordinary `Depends(get_user_db)` session: FastAPI
    closes a dependency-injected session as soon as the route *function* returns,
    which happens immediately after handing back this generator — long before the
    generator itself finishes streaming. Opening the RLS-scoped session directly
    inside the generator keeps it alive for the stream's actual lifetime instead.

    Must be declared before the `/{garment_id}` routes below — FastAPI matches
    routes in registration order, so a literal path like this one has to come
    before a parameterized path that would otherwise swallow it (a request to
    /events would match {garment_id}="events" first and 422 trying to parse
    that as a UUID; live-verified this exact failure on the deployed backend).
    """

    async def event_stream():
        seen: dict[UUID, str] = {}
        elapsed = 0.0
        timeout_seconds = 120.0
        async for db in get_rls_scoped_db(current):
            while elapsed < timeout_seconds:
                rows = list(
                    (
                        await db.execute(
                            select(GarmentImage.id, GarmentImage.garment_id, GarmentImage.status)
                            .join(Garment, Garment.id == GarmentImage.garment_id)
                            .where(Garment.user_id == current.id)
                            .where(GarmentImage.status != "ready")
                        )
                    ).all()
                )
                for image_id, garment_id, status in rows:
                    if seen.get(image_id) != status:
                        seen[image_id] = status
                        payload = {
                            "image_id": str(image_id),
                            "garment_id": str(garment_id),
                            "status": status,
                        }
                        yield f"event: status\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(1.5)
                elapsed += 1.5

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{garment_id}", response_model=GarmentOut)
async def get_garment(
    garment_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> GarmentOut:
    garment = (
        await db.execute(select(Garment).where(Garment.id == garment_id))
    ).scalar_one_or_none()
    if garment is None:
        raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})
    images = list(
        (
            await db.execute(
                select(GarmentImage)
                .where(GarmentImage.garment_id == garment_id)
                .order_by(GarmentImage.sort_order)
            )
        ).scalars()
    )
    garment.images = images

    # See list_garments' matching comment — bucket is private, so raw
    # storage_url paths need signing before they leave the API.
    storage_client = get_storage_client()
    signed = await asyncio.to_thread(
        storage_client.signed_urls, [img.storage_url for img in images]
    )
    result = GarmentOut.model_validate(garment)
    for img in result.images:
        img.storage_url = signed.get(img.storage_url, img.storage_url)
    return result


@router.patch("/{garment_id}", response_model=GarmentOut)
async def update_garment(
    garment_id: UUID,
    body: GarmentUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> Garment:
    garment = (
        await db.execute(select(Garment).where(Garment.id == garment_id))
    ).scalar_one_or_none()
    if garment is None:
        raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(garment, field, value)
    await db.flush()
    await db.refresh(garment)
    garment.images = []
    return garment


@router.delete("/{garment_id}", status_code=204)
async def delete_garment(
    garment_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> None:
    """Hard delete, not archive — the archive toggle already exists via
    PATCH is_archived for the 'keep the record, hide it' case; this is for
    genuinely removing something (wrong upload, duplicate, doesn't exist
    anymore). Cleans up the child rows other tables' non-nullable FKs to
    garments would otherwise reject: outfit_items (dropped — just leaves
    that historical outfit one item short) and wear_logs.garment_id (nulled
    out, not deleted — the wear-count history itself is still meaningful
    even once the garment referenced by it is gone).
    """
    garment = (
        await db.execute(select(Garment).where(Garment.id == garment_id))
    ).scalar_one_or_none()
    if garment is None:
        raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})

    images = list(
        (
            await db.execute(
                select(GarmentImage).where(GarmentImage.garment_id == garment_id)
            )
        ).scalars()
    )
    paths = [img.storage_url for img in images]

    await db.execute(delete(OutfitItem).where(OutfitItem.garment_id == garment_id))
    await db.execute(
        update(WearLog).where(WearLog.garment_id == garment_id).values(garment_id=None)
    )
    await db.execute(delete(GarmentEmbedding).where(GarmentEmbedding.garment_id == garment_id))
    await db.execute(delete(GarmentImage).where(GarmentImage.garment_id == garment_id))
    await db.execute(delete(Garment).where(Garment.id == garment_id))
    await db.commit()

    if paths:
        try:
            await asyncio.to_thread(get_storage_client().remove, paths)
        except Exception:  # noqa: BLE001 — DB delete already committed; a storage
            pass  # cleanup failure shouldn't surface as a failed delete to the user
