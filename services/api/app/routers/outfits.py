import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.integrations.chat import get_outfit_reranker
from app.integrations.storage import get_storage_client
from app.models.garment import Garment, GarmentImage
from app.models.outfit import Outfit, OutfitItem
from app.schemas.outfit import GenerateOutfitRequest, OutfitItemOut, OutfitOut
from app.services.outfit_engine import GenerationContext
from app.services.outfit_service import generate_and_persist

router = APIRouter(prefix="/outfits", tags=["outfits"])


async def _primary_image_map(db: AsyncSession, garment_ids: list[UUID]) -> dict[UUID, str]:
    """Returns signed URLs, not raw storage paths — the bucket is private
    (see storage.py), so a raw path isn't loadable by a browser."""
    if not garment_ids:
        return {}
    rows = list(
        (
            await db.execute(
                select(GarmentImage.garment_id, GarmentImage.storage_url)
                .where(GarmentImage.garment_id.in_(garment_ids))
                .order_by(GarmentImage.is_primary.desc(), GarmentImage.sort_order)
            )
        ).all()
    )
    paths: dict[UUID, str] = {}
    for garment_id, storage_url in rows:
        # first row per garment_id wins — ordered so primary/lowest-sort_order comes first
        paths.setdefault(garment_id, storage_url)
    signed = await asyncio.to_thread(get_storage_client().signed_urls, list(paths.values()))
    return {gid: signed.get(path, path) for gid, path in paths.items()}


@router.post("/generate", response_model=list[OutfitOut])
async def generate(
    body: GenerateOutfitRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> list[OutfitOut]:
    """The Outfit Generator (PRD §6.2/6.3) — hybrid rule engine + Gemini
    re-ranking, see system-architecture.md §5.2."""
    context = GenerationContext(
        occasion=body.occasion,
        season=body.season,
        color_preference=body.color_preference,
        exclude_recently_worn_days=body.exclude_recently_worn_days,
        count=body.count,
    )
    results = await generate_and_persist(db, current.id, context, get_outfit_reranker())
    if not results:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "insufficient_wardrobe",
                "title": "Not enough tagged items to build an outfit yet "
                "(need at least one top+bottom or dress, plus shoes)",
                "status": 422,
            },
        )

    all_garment_ids = [g.id for _, items in results for g in items.values()]
    images = await _primary_image_map(db, all_garment_ids)

    return [
        OutfitOut(
            id=outfit.id,
            source=outfit.source,
            score=outfit.score,
            score_breakdown=outfit.score_breakdown,
            rationale=outfit.rationale,
            is_favorite=outfit.is_favorite,
            created_at=outfit.created_at,
            items=[
                OutfitItemOut(
                    garment_id=g.id,
                    slot=slot,
                    category=g.category,
                    primary_color=g.primary_color,
                    image_url=images.get(g.id),
                )
                for slot, g in items.items()
            ],
        )
        for outfit, items in results
    ]


@router.get("/{outfit_id}", response_model=OutfitOut)
async def get_outfit(
    outfit_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> OutfitOut:
    outfit = (
        await db.execute(select(Outfit).where(Outfit.id == outfit_id))
    ).scalar_one_or_none()
    if outfit is None:
        raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})

    rows = list(
        (
            await db.execute(
                select(OutfitItem.slot, Garment)
                .join(Garment, Garment.id == OutfitItem.garment_id)
                .where(OutfitItem.outfit_id == outfit_id)
            )
        ).all()
    )
    images = await _primary_image_map(db, [g.id for _, g in rows])

    return OutfitOut(
        id=outfit.id,
        source=outfit.source,
        score=outfit.score,
        score_breakdown=outfit.score_breakdown,
        rationale=outfit.rationale,
        is_favorite=outfit.is_favorite,
        created_at=outfit.created_at,
        items=[
            OutfitItemOut(
                garment_id=g.id,
                slot=slot,
                category=g.category,
                primary_color=g.primary_color,
                image_url=images.get(g.id),
            )
            for slot, g in rows
        ],
    )
