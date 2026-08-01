from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.models.outfit import OutfitItem
from app.models.wear_log import WearLog
from app.schemas.outfit import WearLogCreate, WearLogOut

router = APIRouter(prefix="/wear-logs", tags=["wear-logs"])


@router.post("", response_model=list[WearLogOut], status_code=201)
async def log_wear(
    body: WearLogCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> list[WearLog]:
    """One wear_logs row per garment, always — a deliberate simplification vs.
    database-schema.md's nullable-garment-id "log a whole outfit at once" design:
    fewer moving parts (no expansion trigger/view needed), at the cost of a
    handful of duplicate rows per outfit-level log. See migration 0003's
    docstring on garment_wear_stats for the same trade-off reasoning."""
    garment_ids = list(body.garment_ids)
    if not garment_ids and body.outfit_id is not None:
        garment_ids = list(
            (
                await db.execute(
                    select(OutfitItem.garment_id).where(OutfitItem.outfit_id == body.outfit_id)
                )
            ).scalars()
        )
    if not garment_ids:
        raise HTTPException(
            status_code=400,
            detail={"type": "no_garments", "title": "No garments to log", "status": 400},
        )

    worn_on = body.worn_on or date.today()
    logs = [
        WearLog(
            user_id=current.id,
            garment_id=garment_id,
            outfit_id=body.outfit_id,
            worn_on=worn_on,
            notes=body.notes,
        )
        for garment_id in garment_ids
    ]
    db.add_all(logs)
    await db.flush()
    for log in logs:
        await db.refresh(log)
    return logs


@router.get("", response_model=list[WearLogOut])
async def list_wear_logs(
    garment_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> list[WearLog]:
    stmt = select(WearLog).order_by(WearLog.worn_on.desc()).limit(limit)
    if garment_id:
        stmt = stmt.where(WearLog.garment_id == garment_id)
    return list((await db.execute(stmt)).scalars())
