import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Brand(Base):
    """See database-schema.md `brands`. Not user-scoped — shared lookup table,
    no RLS needed (nothing sensitive, nothing owned by a single user)."""

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    tier: Mapped[str | None] = mapped_column(String, nullable=True)
