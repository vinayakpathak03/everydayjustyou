import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.models.wear_log import WearLog
from app.schemas.outfit import WearLogCreate, WearLogOut
from app.services.wear_log_service import log_wear

router = APIRouter(prefix="/wear-logs", tags=["wear-logs"])


@router.post("", response_model=list[WearLogOut], status_code=201)
async def create_wear_logs(
    body: WearLogCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> list[WearLog]:
    logs = await log_wear(
        db,
        uuid.UUID(current.id),
        garment_ids=body.garment_ids,
        outfit_id=body.outfit_id,
        worn_on=body.worn_on,
        notes=body.notes,
    )
    if not logs:
        raise HTTPException(
            status_code=400,
            detail={"type": "no_garments", "title": "No garments to log", "status": 400},
        )
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
