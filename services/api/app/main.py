import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, garments, internal, users
from app.workers.poller import run_forever

settings = get_settings()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The in-process job poller — not a separate worker service, see
    # docs/architecture/system-architecture.md §3. Started/stopped alongside the
    # API process itself since there's only one process to begin with.
    stop_event = asyncio.Event()
    poller_task = asyncio.create_task(run_forever(stop_event))
    logger.info("processing_jobs poller started")
    yield
    stop_event.set()
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass
    logger.info("processing_jobs poller stopped")


app = FastAPI(title="Muse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(garments.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1")
