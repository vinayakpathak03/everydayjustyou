from uuid import UUID

from pydantic import BaseModel


class WearStatEntry(BaseModel):
    garment_id: UUID
    category: str
    primary_color: str | None
    times_worn: int
    last_worn_on: str | None = None
    cost_per_wear: float | None = None


class AnalyticsSummary(BaseModel):
    most_worn: list[WearStatEntry]
    least_worn: list[WearStatEntry]
    cost_per_wear: list[WearStatEntry]
