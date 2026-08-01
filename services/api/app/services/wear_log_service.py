from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outfit import OutfitItem
from app.models.wear_log import WearLog

# Shared by routers/wear_logs.py (POST /wear-logs) and the Stylist chat's
# log_wear tool (app/services/stylist_tools.py) — one place for the "one row
# per garment, always" simplification documented in routers/wear_logs.py.


async def log_wear(
    db: AsyncSession,
    user_id: UUID,
    *,
    garment_ids: list[UUID] | None = None,
    outfit_id: UUID | None = None,
    worn_on: date | None = None,
    notes: str | None = None,
) -> list[WearLog]:
    resolved_ids = list(garment_ids or [])
    if not resolved_ids and outfit_id is not None:
        resolved_ids = list(
            (
                await db.execute(
                    select(OutfitItem.garment_id).where(OutfitItem.outfit_id == outfit_id)
                )
            ).scalars()
        )
    if not resolved_ids:
        return []

    worn_on = worn_on or date.today()
    logs = [
        WearLog(user_id=user_id, garment_id=gid, outfit_id=outfit_id, worn_on=worn_on, notes=notes)
        for gid in resolved_ids
    ]
    db.add_all(logs)
    await db.flush()
    for log in logs:
        await db.refresh(log)
    return logs
