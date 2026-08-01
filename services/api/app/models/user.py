import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Profile row for a Supabase Auth user. `id` is the *same* UUID as the
    corresponding `auth.users.id` — Supabase Auth owns credentials/sessions,
    this table owns everything app-specific. See database-schema.md `users`."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, nullable=False, server_default="UTC")
    notification_time: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_dev_photo_access: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    tc_version: Mapped[str | None] = mapped_column(String, nullable=True)
    tc_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
