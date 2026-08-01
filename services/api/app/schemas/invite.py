from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class InviteCreate(BaseModel):
    email: EmailStr


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    token: str
    status: str
    expires_at: datetime | None
    created_at: datetime


class InviteValidateOut(BaseModel):
    valid: bool
    email: str | None = None
    reason: str | None = None


class InviteAccept(BaseModel):
    token: str
