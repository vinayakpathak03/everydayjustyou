import asyncio
import logging

from sqlalchemy import select

from app.db.session import AdminSessionLocal
from app.integrations.background_removal import RembgBackgroundRemover
from app.integrations.embeddings import get_embedding_store
from app.integrations.storage import get_storage_client
from app.integrations.vision import get_attribute_extractor
from app.models.processing_job import ProcessingJob
from app.workers.jobs import process_image

logger = logging.getLogger("app.workers.poller")

POLL_INTERVAL_SECONDS = 3
BATCH_SIZE = 5
MAX_ATTEMPTS = 3

_background_remover = RembgBackgroundRemover()


async def _dispatch(job: ProcessingJob, db) -> None:
    if job.type == "process_image":
        await process_image.run(
            job.payload,
            db,
            background_remover=_background_remover,
            attribute_extractor=get_attribute_extractor(),
            embedding_store=get_embedding_store(),
            storage_client=get_storage_client(),
        )
    else:
        raise ValueError(f"Unknown job type: {job.type}")


async def poll_once() -> int:
    """Runs against the admin session deliberately: this is a system process
    handling every user's jobs, not a per-user request — the one other
    legitimate use of elevated access alongside invite redemption (see
    docs/architecture/database-schema.md §9). Returns the number of jobs processed."""
    async with AdminSessionLocal() as db:
        # FOR UPDATE SKIP LOCKED: safe to eventually run more than one poller
        # instance without double-processing a job, even though Phase 1 only
        # ever runs one (single deployable, see system-architecture.md §3).
        result = await db.execute(
            select(ProcessingJob)
            .where(ProcessingJob.status == "pending")
            .order_by(ProcessingJob.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars())
        for job in jobs:
            job.status = "running"
        await db.commit()

    processed = 0
    for job in jobs:
        async with AdminSessionLocal() as db:
            fresh = await db.get(ProcessingJob, job.id)
            if fresh is None:
                continue  # deleted between claim and dispatch — nothing to do
            try:
                await _dispatch(fresh, db)
                fresh.status = "done"
                await db.commit()
            except Exception as exc:  # noqa: BLE001 — job failures must not kill the poller
                await db.rollback()
                async with AdminSessionLocal() as retry_db:
                    retry_job = await retry_db.get(ProcessingJob, job.id)
                    if retry_job is not None:
                        retry_job.attempts += 1
                        retry_job.error = str(exc)[:500]
                        retry_job.status = (
                            "failed" if retry_job.attempts >= MAX_ATTEMPTS else "pending"
                        )
                        await retry_db.commit()
                logger.exception("Job %s (%s) failed", job.id, job.type)
            processed += 1
    return processed


async def run_forever(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            processed = await poll_once()
        except Exception:  # noqa: BLE001 — a bad poll must not kill the loop itself
            logger.exception("processing_jobs poll failed")
            processed = 0
        if processed == 0:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL_SECONDS)
            except TimeoutError:
                pass
