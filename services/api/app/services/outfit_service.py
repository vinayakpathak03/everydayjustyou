import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.chat import OutfitReranker
from app.models.garment import Garment
from app.models.outfit import Outfit, OutfitItem
from app.models.wear_log import WearLog
from app.services.outfit_engine import (
    GenerationContext,
    OutfitCandidate,
    generate_outfits,
    group_by_category,
)

logger = logging.getLogger("app.services.outfit")

RERANK_POOL_SIZE = 10  # top-K sent to the LLM — see chat.py's docstring
WEAR_LOOKBACK_DAYS = 90


async def _eligible_garments(db: AsyncSession, user_id) -> list[Garment]:
    stmt = select(Garment).where(
        Garment.user_id == user_id,
        Garment.is_archived.is_(False),
        Garment.sensitive_category.is_(False),  # hard exclude — see PRD §7.1 item 4
        Garment.status != "processing",
    )
    return list((await db.execute(stmt)).scalars())


async def _last_worn_map(db: AsyncSession, user_id) -> dict:
    cutoff = date.today() - timedelta(days=WEAR_LOOKBACK_DAYS)
    stmt = select(WearLog.garment_id, WearLog.worn_on).where(
        WearLog.user_id == user_id,
        WearLog.worn_on >= cutoff,
        WearLog.garment_id.is_not(None),
    )
    rows = (await db.execute(stmt)).all()
    last_worn: dict = {}
    for garment_id, worn_on in rows:
        if garment_id not in last_worn or worn_on > last_worn[garment_id]:
            last_worn[garment_id] = worn_on
    return last_worn


async def _apply_rerank(
    candidates: list[OutfitCandidate], context: GenerationContext, reranker: OutfitReranker
) -> list[tuple[OutfitCandidate, str | None]]:
    """Blends the LLM's qualitative judgment into the rule score and reorders —
    falls back to pure rule-ranking if the Gemini call fails for any reason
    (rate limit, network, malformed response), since a generated outfit that's
    merely un-explained is far better than a 500 on the whole request."""
    pool = candidates[:RERANK_POOL_SIZE]
    try:
        result = await reranker.rerank(pool, context.count)
    except Exception:  # noqa: BLE001 — reranking is an enhancement, not required for a valid response
        logger.exception("Outfit reranking failed; falling back to rule-only ranking")
        return [(c, None) for c in candidates[: context.count]]

    reranked: list[tuple[OutfitCandidate, str | None]] = []
    for pick in result.picks:
        if not (0 <= pick.candidate_index < len(pool)):
            continue
        candidate = pool[pick.candidate_index]
        candidate.score = round(candidate.score * 0.6 + pick.qualitative_score * 0.4)
        reranked.append((candidate, pick.rationale))
    return reranked or [(c, None) for c in candidates[: context.count]]


async def generate_and_persist(
    db: AsyncSession,
    user_id,
    context: GenerationContext,
    reranker: OutfitReranker,
) -> list[tuple[Outfit, dict[str, Garment]]]:
    """Returns each persisted Outfit alongside its {slot: Garment} mapping — the
    router builds response items straight from these already-loaded Garment
    objects instead of re-querying, since generate_outfits() already fetched them."""
    garments = await _eligible_garments(db, user_id)
    by_category = group_by_category(garments)
    last_worn = await _last_worn_map(db, user_id)

    candidates = generate_outfits(by_category, context, last_worn)
    if not candidates:
        return []

    final_candidates = await _apply_rerank(candidates, context, reranker)

    saved: list[tuple[Outfit, dict[str, Garment]]] = []
    for candidate, rationale in final_candidates:
        outfit = Outfit(
            user_id=user_id,
            source="generated",
            context={
                "occasion": context.occasion,
                "season": context.season,
                "color_preference": context.color_preference,
            },
            score=candidate.score,
            score_breakdown=candidate.breakdown,
            rationale=rationale,
        )
        db.add(outfit)
        await db.flush()
        for slot, garment in candidate.items.items():
            db.add(OutfitItem(outfit_id=outfit.id, garment_id=garment.id, slot=slot))
        saved.append((outfit, candidate.items))
    await db.flush()
    return saved
