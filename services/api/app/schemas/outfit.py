from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenerateOutfitRequest(BaseModel):
    occasion: str | None = None
    season: str | None = None
    color_preference: str | None = None
    exclude_recently_worn_days: int = Field(default=7, ge=0, le=90)
    count: int = Field(default=3, ge=1, le=6)


class OutfitItemOut(BaseModel):
    garment_id: UUID
    slot: str
    category: str
    primary_color: str | None
    image_url: str | None = None


class OutfitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    score: int
    score_breakdown: dict | None
    rationale: str | None
    is_favorite: bool
    created_at: datetime
    items: list[OutfitItemOut] = Field(default_factory=list)


class WearLogCreate(BaseModel):
    garment_ids: list[UUID] = Field(default_factory=list)
    outfit_id: UUID | None = None
    worn_on: date | None = None
    notes: str | None = None


class WearLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_id: UUID | None
    outfit_id: UUID | None
    worn_on: date
    notes: str | None
