from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GarmentImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    storage_url: str
    status: str
    is_primary: bool
    sort_order: int


class GarmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    subcategory: str | None
    primary_color: str | None
    secondary_colors: list[str] | None
    pattern: str | None
    fabric_guess: str | None
    fabric_confidence: str | None
    sleeve_length: str | None
    neckline: str | None
    fit: str | None
    season: list[str] | None
    occasion: list[str] | None
    formality_score: int | None
    color_hex: str | None
    acquisition_type: str | None
    is_favorite: bool
    is_archived: bool
    ai_description: str | None
    ai_confidence: dict | None
    status: str
    entry_mode: str
    sensitive_category: bool
    manual_description: str | None
    manual_quantity: int | None
    created_at: datetime
    images: list[GarmentImageOut] = Field(default_factory=list)


class GarmentImageUploadOut(BaseModel):
    garment_id: UUID
    image_id: UUID
    status: str


class GarmentUpdate(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    primary_color: str | None = None
    secondary_colors: list[str] | None = None
    pattern: str | None = None
    fabric_guess: str | None = None
    sleeve_length: str | None = None
    neckline: str | None = None
    fit: str | None = None
    season: list[str] | None = None
    occasion: list[str] | None = None
    formality_score: int | None = None
    color_hex: str | None = None
    acquisition_type: str | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None


class GarmentManualCreate(BaseModel):
    """Sensitive-category manual entry — see PRD §7.1 item 4. No image field here
    on purpose: a photo, if any, goes through a separate optional upload step that
    explicitly bypasses rembg/Gemini (see routers/garments.py)."""

    category: str
    manual_description: str = Field(min_length=1, max_length=500)
    manual_quantity: int | None = Field(default=None, ge=1)
    color_hex: str | None = None
    sensitive_category: bool = True
