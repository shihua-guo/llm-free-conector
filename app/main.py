import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import admin, health, models, openai
from app.core.config import settings
from app.db.init import init_db
from app.db.session import SessionLocal
from app.services.newapi_client import NewAPIClient
from app.services.sync import ModelSyncService

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


async def _sync_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.sync_interval_seconds)
            continue
        except TimeoutError:
            pass

        try:
            async with SessionLocal() as session:
                summary = await ModelSyncService(session, NewAPIClient()).sync()
                logger.info("model sync completed: %s", summary)
        except Exception:
            logger.exception("model sync failed")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_db()

    if settings.sync_on_startup:
        try:
            async with SessionLocal() as session:
                summary = await ModelSyncService(session, NewAPIClient()).sync()
                logger.info("startup model sync completed: %s", summary)
        except Exception:
            logger.exception("startup model sync failed")

    stop_event = asyncio.Event()
    task: asyncio.Task[None] | None = None
    if settings.enable_background_sync:
        task = asyncio.create_task(_sync_loop(stop_event))

    try:
        yield
    finally:
        stop_event.set()
        if task:
            await task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(models.router)
app.include_router(openai.router)
