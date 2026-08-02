import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.background_removal import BackgroundRemover
from app.integrations.embeddings import TEXT_EMBEDDING_MODEL, EmbeddingStore
from app.integrations.storage import StorageClient
from app.integrations.vision import AttributeExtractor
from app.models.garment import Garment, GarmentEmbedding, GarmentImage

PROCESSED_CONTENT_TYPE = "image/png"


async def run(
    payload: dict,
    db: AsyncSession,
    *,
    background_remover: BackgroundRemover,
    attribute_extractor: AttributeExtractor,
    embedding_store: EmbeddingStore,
    storage_client: StorageClient,
) -> None:
    """The `process_image` job: raw photo -> bg-removed -> Gemini-tagged -> embedded.
    Mirrors the sequence diagram in docs/architecture/system-architecture.md §5.1.
    Runs inside the in-process asyncio poller (app/workers/poller.py), not a
    separate worker service — see system-architecture.md §3.

    Never invoked for sensitive-category items: those are created via
    POST /garments/manual, which never enqueues a processing_jobs row at all.
    """
    image_id = uuid.UUID(payload["garment_image_id"])
    image = (
        await db.execute(select(GarmentImage).where(GarmentImage.id == image_id))
    ).scalar_one()
    garment = (
        await db.execute(select(Garment).where(Garment.id == image.garment_id))
    ).scalar_one()

    raw_bytes = await asyncio.to_thread(storage_client.download, image.storage_url)

    processed_bytes = await asyncio.to_thread(background_remover.remove, raw_bytes)
    processed_path = f"{garment.user_id}/{garment.id}/{image.id}-processed.png"
    await asyncio.to_thread(
        storage_client.upload, processed_path, processed_bytes, PROCESSED_CONTENT_TYPE
    )
    image.storage_url = processed_path
    image.kind = "processed"
    image.status = "bg_removed"
    await db.flush()

    extraction = await attribute_extractor.extract(processed_bytes, PROCESSED_CONTENT_TYPE)
    garment.category = extraction.category
    garment.subcategory = extraction.subcategory
    garment.primary_color = extraction.primary_color
    garment.secondary_colors = extraction.secondary_colors or None
    garment.pattern = extraction.pattern
    garment.fabric_guess = extraction.fabric_guess
    garment.fabric_confidence = extraction.fabric_confidence
    garment.sleeve_length = extraction.sleeve_length
    garment.neckline = extraction.neckline
    garment.fit = extraction.fit
    garment.season = extraction.season or None
    garment.occasion = extraction.occasion or None
    garment.formality_score = extraction.formality_score
    garment.ai_description = extraction.description
    garment.status = "needs_review"
    image.status = "tagged"
    await db.flush()

    embedding_vector = await embedding_store.embed_text(extraction.description)
    db.add(
        GarmentEmbedding(
            garment_id=garment.id,
            kind="text_description",
            embedding=embedding_vector,
            model=TEXT_EMBEDDING_MODEL,
        )
    )
    await db.flush()
