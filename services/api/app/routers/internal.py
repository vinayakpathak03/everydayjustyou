from fastapi import APIRouter, Depends

from app.core.security import verify_cron_secret

router = APIRouter(tags=["internal"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/internal/cron/daily-notifications", dependencies=[Depends(verify_cron_secret)])
async def daily_notifications() -> dict:
    """Pinged by the GitHub Actions `schedule:` workflow — see system-architecture.md
    §4. No-op until Phase 5 (Daily Outfit Notification) lands; wired now so the cron
    plumbing and auth can be tested independently of the feature itself."""
    return {"status": "not_implemented_yet"}
