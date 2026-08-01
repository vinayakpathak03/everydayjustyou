import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Outfit(Base):
    """See database-schema.md `outfits`."""

    __tablename__ = "outfits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, server_default="generated")
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rationale: Mapped[str | None] = mapped_column(String, nullable=True)
    collage_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    canvas_layout: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["OutfitItem"]] = relationship(
        "OutfitItem", viewonly=True, lazy="noload"
    )


class OutfitItem(Base):
    """See database-schema.md `outfit_items`."""

    __tablename__ = "outfit_items"

    outfit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outfits.id"), primary_key=True
    )
    garment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("garments.id"), primary_key=True
    )
    slot: Mapped[str] = mapped_column(String, primary_key=True)
