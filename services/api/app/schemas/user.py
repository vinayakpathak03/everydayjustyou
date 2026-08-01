from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None
    onboarding_completed_at: datetime | None
    consent_dev_photo_access: bool
    tc_accepted_at: datetime | None


class UserUpdate(BaseModel):
    display_name: str | None = None
    timezone: str | None = None
    notification_time: str | None = None
    location: dict | None = None


class ConsentIn(BaseModel):
    consent_dev_photo_access: bool
    tc_version: str


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consent_dev_photo_access: bool
    tc_version: str | None
    tc_accepted_at: datetime | None
    onboarding_completed_at: datetime | None
