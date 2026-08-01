import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StyleProfile(Base):
    """One-to-one with users. See database-schema.md `style_profiles`."""

    __tablename__ = "style_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    preferred_colors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    preferred_aesthetics: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    sizes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dislikes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
