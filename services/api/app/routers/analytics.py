from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.schemas.analytics import AnalyticsSummary, WearStatEntry

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Reads the `garment_wear_stats` view (migration 0003) — a plain view, so RLS
# on the underlying garments/wear_logs tables applies exactly as if these
# columns were selected directly from them (no SECURITY DEFINER bypass).
BASE_QUERY = """
    select ws.garment_id, g.category, g.primary_color, ws.times_worn,
           ws.last_worn_on, ws.cost_per_wear
    from garment_wear_stats ws
    join garments g on g.id = ws.garment_id
    where g.is_archived = false and g.sensitive_category = false
"""


def _row_to_entry(row) -> WearStatEntry:
    return WearStatEntry(
        garment_id=row.garment_id,
        category=row.category,
        primary_color=row.primary_color,
        times_worn=row.times_worn,
        last_worn_on=row.last_worn_on.isoformat() if row.last_worn_on else None,
        cost_per_wear=float(row.cost_per_wear) if row.cost_per_wear is not None else None,
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> AnalyticsSummary:
    most_worn_rows = (
        await db.execute(text(f"{BASE_QUERY} order by ws.times_worn desc limit 10"))
    ).all()
    least_worn_rows = (
        await db.execute(
            text(f"{BASE_QUERY} order by ws.times_worn asc, g.created_at asc limit 10")
        )
    ).all()
    cost_per_wear_rows = (
        await db.execute(
            text(
                f"{BASE_QUERY} and ws.cost_per_wear is not null "
                "order by ws.cost_per_wear asc limit 10"
            )
        )
    ).all()

    return AnalyticsSummary(
        most_worn=[_row_to_entry(r) for r in most_worn_rows],
        least_worn=[_row_to_entry(r) for r in least_worn_rows],
        cost_per_wear=[_row_to_entry(r) for r in cost_per_wear_rows],
    )
